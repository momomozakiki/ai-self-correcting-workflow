#!/usr/bin/env python3
"""Adaptive Self-Correcting Workflow -- hook dispatcher.

A single fail-soft dispatcher invoked by Claude Code for the ``SessionStart``,
``PreToolUse``, ``PostToolUse`` and ``Stop`` hook events. It reads the event JSON from stdin,
loads the project's ``workflow_config.json`` and branches to the appropriate
handler. Every handler is wrapped so the process *always* exits 0 -- a bug in
the workflow tooling must never break a coding session.

Stdlib only (Python 3.8+). No third-party dependencies, so projects can vendor
this file as a git submodule without inheriting a dependency tree.

See ``schemas/hook_contract.md`` for the input/output contracts and
``GUIDE.md`` section 7 for the full behavioural spec.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Tuple

STATE_TTL_SECONDS = 24 * 60 * 60  # stale session state older than this is purged
DEFAULT_MAX_BLOCKS = 2
DEFAULT_MAIN_BRANCH = "main"

# --- loop detection (v14 section 15.4) ------------------------------------- #
DEFAULT_LOOP_THRESHOLD = 3           # consecutive identical calls before we speak up
DEFAULT_LOOP_LOG = ".ai/08-behavioral-metrics/loop_detection.jsonl"
LOOP_WINDOW = 20                     # how many recent call signatures we keep

# --- governance library ----------------------------------------------------- #
DEFAULT_LIBRARY_ROOT = ".ai"
# DEFAULT_MATURITY_TRACKER removed 2026-08-29 with the maturity ladder it fed.


# --------------------------------------------------------------------------- #
# Config discovery & loading
# --------------------------------------------------------------------------- #
def find_config_path() -> Optional[Path]:
    """Locate ``workflow_config.json``.

    Primary: ``$CLAUDE_PROJECT_DIR`` (set by Claude Code to the project root,
    correct even when this hook lives deep inside ``.claude/workflow-core/``).
    Fallback: walk upward from this file looking for ``.claude/workflow_config.json``
    or a repo-root ``workflow_config.json`` (covers self-dogfooding, where the
    hook sits at the repo root).
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        candidate = Path(project_dir) / ".claude" / "workflow_config.json"
        if candidate.is_file():
            return candidate
        candidate = Path(project_dir) / "workflow_config.json"
        if candidate.is_file():
            return candidate

    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        for candidate in (
            parent / ".claude" / "workflow_config.json",
            parent / "workflow_config.json",
        ):
            if candidate.is_file():
                return candidate
    return None


#: ``Verified 2026-08-06 against Claude Code v2.1.223``. Kept identical to
#: ``tests/test_skills.py::VerificationStamps.STAMP`` -- the test enforces the
#: shape, ``--self-test`` reports the age, and they must read the same thing.
STAMP_RE = re.compile(
    r"[Vv]erified\s+(?:on\s+)?\*{0,2}(\d{4}-\d{2}-\d{2})\*{0,2}\s+against\s+"
    r"(?:Claude Code\s+)?\*{0,2}v(\d+\.\d+\.\d+)\*{0,2}")


def find_schema_path() -> Optional[Path]:
    """Locate ``schemas/config_schema.json`` by walking upward from this file.

    This was ``__file__.parent.parent / "schemas"``, which silently depended on
    the dispatcher sitting exactly one directory below the repository root.
    Moving it from ``hooks/`` to ``.claude/hooks/`` made that resolve to
    ``.claude/schemas/``, and because a missing schema only *warns*,
    ``--self-test`` went on reporting ``RESULT: PASS`` with validation skipped
    entirely. An upward walk holds for both layouts, including an adopter's
    ``.claude/workflow-core/.claude/hooks/``.
    """
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "schemas" / "config_schema.json"
        if candidate.is_file():
            return candidate
    return None


def load_config() -> Tuple[Dict[str, Any], Path]:
    """Return (config dict, project_root). Always returns a usable config."""
    config_path = find_config_path()
    if config_path is None:
        return {}, Path(os.environ.get("CLAUDE_PROJECT_DIR") or ".").resolve()

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        config = {}

    # Project root: explicit config value wins, else the dir containing .claude/,
    # else the config file's directory.
    root_hint = config.get("project_root")
    if root_hint and root_hint != ".":
        project_root = (config_path.parent / root_hint).resolve()
    elif config_path.parent.name == ".claude":
        project_root = config_path.parent.parent.resolve()
    else:
        project_root = config_path.parent.resolve()
    return config, project_root


# --------------------------------------------------------------------------- #
# Per-session state
# --------------------------------------------------------------------------- #
def _sanitize(session_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)[:128]


def state_path(session_id: str) -> Path:
    return Path(tempfile.gettempdir()) / f"workflow_hook_state_{_sanitize(session_id)}.json"


def default_state() -> Dict[str, Any]:
    return {
        "source_changed": False,
        "ledger_touched": False,
        "stop_block_count": 0,
        "doc_nudged": False,
        "skill_nudged": False,
        "main_branch_detected": None,  # memoised by resolve_main_branch() on first Stop
        "recent_tool_calls": [],       # rolling window of tool-call signatures
        "loop_hits": [],               # signatures already reported this session
        "session_start_ts": time.time(),
    }


def load_state(session_id: Optional[str]) -> Dict[str, Any]:
    if not session_id:
        return default_state()
    try:
        return json.loads(state_path(session_id).read_text(encoding="utf-8"))
    except Exception:
        return default_state()


def save_state(session_id: Optional[str], state: Dict[str, Any]) -> None:
    if not session_id:
        return
    try:
        path = state_path(session_id)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state), encoding="utf-8")
        os.replace(tmp, path)  # atomic on the same filesystem
    except Exception:
        pass


def purge_stale_state() -> None:
    """Remove session state files older than the TTL."""
    try:
        now = time.time()
        for f in Path(tempfile.gettempdir()).glob("workflow_hook_state_*.json"):
            try:
                if now - f.stat().st_mtime > STATE_TTL_SECONDS:
                    f.unlink()
            except Exception:
                continue
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Git helpers (all guarded -- never raise)
# --------------------------------------------------------------------------- #
def _git(project_root: Path, *args: str) -> Optional[str]:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if out.returncode != 0:
            return None
        return out.stdout.strip()
    except Exception:
        return None


def git_status(project_root: Path) -> Dict[str, Any]:
    branch = _git(project_root, "rev-parse", "--abbrev-ref", "HEAD")
    dirty = bool(_git(project_root, "status", "--porcelain"))
    ahead = behind = None
    counts = _git(project_root, "rev-list", "--left-right", "--count", "@{u}...HEAD")
    if counts:
        parts = counts.split()
        if len(parts) == 2:
            behind, ahead = parts[0], parts[1]
    return {"branch": branch, "dirty": dirty, "ahead": ahead, "behind": behind}


def detect_main_branch(project_root: Path, remote: str = "origin",
                       probe_remote: bool = False) -> Optional[str]:
    """Best-effort detection of the repository's default branch.

    Two probes, cheapest first:

    1. ``git symbolic-ref refs/remotes/<remote>/HEAD`` -- a purely local ref
       read (no network), set by ``git clone`` and refreshable with
       ``git remote set-head <remote> --auto``.
    2. ``git remote show <remote>`` -- authoritative but **contacts the
       remote**, so it only runs when ``probe_remote`` is true.

    Returns the branch name, or ``None`` when neither probe yields one (caller
    falls back to :data:`DEFAULT_MAIN_BRANCH`). Never raises.
    """
    ref = _git(project_root, "symbolic-ref", "--short", f"refs/remotes/{remote}/HEAD")
    if ref:
        # "origin/main" -> "main"; a bare "main" (no prefix) is used as-is.
        name = ref.split("/", 1)[1] if ref.startswith(remote + "/") else ref
        if name and name != "HEAD":
            return name

    if not probe_remote:
        return None

    shown = _git(project_root, "remote", "show", remote)
    for line in (shown or "").splitlines():
        line = line.strip()
        if line.startswith("HEAD branch:"):
            name = line.split(":", 1)[1].strip()
            # git prints "(unknown)" when the remote HEAD is not resolvable.
            if name and not name.startswith("("):
                return name
    return None


def resolve_main_branch(config: Dict[str, Any], project_root: Path,
                        state: Optional[Dict[str, Any]] = None) -> str:
    """Return the branch treated as "main" for the dirty-tree Stop reminder.

    Precedence:

    1. An explicit, non-empty ``stop_hook.main_branch`` -- always wins, so a
       pinned config is never overridden by detection.
    2. Auto-detection via :func:`detect_main_branch`, unless
       ``stop_hook.main_branch_autodetect`` is false.
    3. :data:`DEFAULT_MAIN_BRANCH`.

    When ``state`` is supplied the detected value is memoised in it under
    ``main_branch_detected`` so repeated Stop events in one session re-use the
    first probe instead of shelling out to git again.
    """
    stop_cfg = config.get("stop_hook") or {}

    explicit = stop_cfg.get("main_branch")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()

    if not stop_cfg.get("main_branch_autodetect", True):
        return DEFAULT_MAIN_BRANCH

    if state is not None:
        cached = state.get("main_branch_detected")
        if isinstance(cached, str) and cached:
            return cached

    detected = detect_main_branch(
        project_root,
        remote=stop_cfg.get("main_branch_remote") or "origin",
        probe_remote=bool(stop_cfg.get("main_branch_probe_remote")),
    ) or DEFAULT_MAIN_BRANCH

    if state is not None:
        state["main_branch_detected"] = detected
    return detected


# --------------------------------------------------------------------------- #
# F5: daily workflow-core update check (opt-in)
# --------------------------------------------------------------------------- #
def check_workflow_updates(config: Dict[str, Any], project_root: Path) -> Optional[str]:
    """Return an F5 update notice if the vendored ``workflow-core`` is behind.

    Opt-in and fail-soft: returns ``None`` (silent) unless
    ``workflow_update_check.enabled`` is true, the submodule is actually linked,
    and a once-per-day fetch finds new upstream commits. Never auto-applies the
    update -- detection & notification only (the agent asks the user per F5).
    """
    cfg = config.get("workflow_update_check") or {}
    if not cfg.get("enabled"):
        return None

    submodule_rel = cfg.get("submodule_path", ".claude/workflow-core")
    remote = cfg.get("remote", "origin")
    branch = cfg.get("branch", "main")

    submodule = (project_root / submodule_rel).resolve()
    if not (submodule / ".git").exists():
        return None  # not linked -- nothing to check

    # Once-per-day gate via a project-persistent state file (survives sessions).
    today = time.strftime("%Y-%m-%d")
    date_file = project_root / ".ai" / ".workflow_check_date"
    try:
        if date_file.read_text(encoding="utf-8").strip() == today:
            return None  # already checked today
    except Exception:
        pass  # missing/unreadable -> proceed with the check

    if _git(submodule, "fetch", "--depth=1", remote, branch) is None:
        return None  # offline or fetch failed -- stay silent

    count = _git(submodule, "rev-list", "--count", f"HEAD..{remote}/{branch}")

    # Record today's check regardless of the outcome, so we don't refetch today.
    try:
        date_file.parent.mkdir(parents=True, exist_ok=True)
        date_file.write_text(today + "\n", encoding="utf-8")
    except Exception:
        pass

    if count and count.strip().isdigit() and int(count) > 0:
        return (
            f"🔄 Workflow updates available ({count} new commits) in "
            f"`{submodule_rel}`. F5: I can run `git submodule update --remote` "
            "and re-validate any new mandatory steps."
        )
    return None


# --------------------------------------------------------------------------- #
# Phase-3 breadcrumb (Stop hook)
# --------------------------------------------------------------------------- #
BREADCRUMB_MARKER = "<!-- workflow-hook: auto-breadcrumb -->"
BREADCRUMB_PATH = "plans/UNFINISHED.md"


def has_outstanding_plan(project_root: Path) -> bool:
    """True if ``plans/UNFINISHED.md`` holds a *human* plan owed attention.

    One definition, used by ``SessionStart`` (F4) and ``--self-test`` alike. The
    hook's own breadcrumb does not count: it reports a dirty tree, and treating
    it as an outstanding plan double-counts the very thing that produced it.
    """
    target = project_root / BREADCRUMB_PATH
    if not target.is_file():
        return False
    try:
        return BREADCRUMB_MARKER not in target.read_text(encoding="utf-8")
    except Exception:
        return True  # unreadable -- surface it rather than swallow it


def skills_dir_exists(project_root: Path) -> bool:
    """True if this project has a ``.claude/skills/`` directory.

    Gates the ``SessionStart`` ``reloadSkills`` flag. Asking for a reload in a
    project with no skills would be a scan that can only ever find nothing, and
    the flag should mean something when it appears.
    """
    try:
        return (project_root / ".claude" / "skills").is_dir()
    except Exception:
        return False


def dirty_excluding_breadcrumb(project_root: Path) -> bool:
    """True if the tree has uncommitted work *other than* our own breadcrumb.

    The Stop hook writes ``plans/UNFINISHED.md`` when the tree is dirty. That
    file is itself untracked, so a naive dirty check sees it next session and
    reports it as more unfinished work -- a loop that manufactures the state it
    complains about and can never clear on its own.

    ``BREADCRUMB_MARKER`` already distinguishes our file from a human-authored
    plan (``write_unfinished_breadcrumb`` refuses to overwrite one), so the same
    marker settles this. A human plan at that path is real uncommitted work and
    still counts.
    """
    # -uall so git lists untracked files individually. Without it a wholly
    # untracked `plans/` collapses to one "plans/" entry, and the breadcrumb
    # inside it becomes indistinguishable from a directory of real work.
    porcelain = _git(project_root, "status", "--porcelain", "-uall") or ""
    for line in porcelain.splitlines():
        path = line[3:].strip().strip('"')
        if PurePosixPath(path.replace("\\", "/")).as_posix() != BREADCRUMB_PATH:
            return True
        target = project_root / BREADCRUMB_PATH
        try:
            if BREADCRUMB_MARKER not in target.read_text(encoding="utf-8"):
                return True  # a human wrote this; it is real work
        except Exception:
            return True  # unreadable -- assume it matters
    return False


def write_unfinished_breadcrumb(project_root: Path, gs: Dict[str, Any],
                                reminders: List[str]) -> None:
    """Record an interrupted Phase-3 closure to ``plans/UNFINISHED.md``.

    Durable safety net: if a session ends with a dirty tree, the next
    ``SessionStart`` (F4) surfaces this file. Fail-soft and idempotent -- it
    overwrites only its own marked breadcrumb and never clobbers a
    human-authored plan (a file lacking ``BREADCRUMB_MARKER`` is left untouched).
    """
    try:
        target = project_root / "plans" / "UNFINISHED.md"
        if target.is_file():
            try:
                existing = target.read_text(encoding="utf-8")
            except Exception:
                existing = ""
            if BREADCRUMB_MARKER not in existing:
                return  # genuine, human-authored plan -- do not overwrite

        porcelain = _git(project_root, "status", "--porcelain") or ""
        files = "\n".join(f"  {line}" for line in porcelain.splitlines()) or "  (none reported)"
        stamp = time.strftime("%Y-%m-%d %H:%M:%S")
        branch = gs.get("branch") or "(unknown)"
        pending = "\n".join(f"- {r}" for r in reminders) or "- Commit & push pending work."

        body = (
            f"{BREADCRUMB_MARKER}\n"
            f"# Unfinished session — auto-recorded {stamp}\n\n"
            "> This breadcrumb was written by the workflow Stop hook because the\n"
            "> working tree was dirty at session end (Phase 3 not completed).\n"
            "> Review, finish closure, then delete this file. It will be\n"
            "> overwritten by the hook while it remains a breadcrumb, but a\n"
            "> human-authored plan placed here is never overwritten.\n\n"
            f"**Branch:** `{branch}`\n\n"
            "**Pending closure steps:**\n"
            f"{pending}\n\n"
            "**Uncommitted files (`git status --porcelain`):**\n\n"
            f"```\n{files}\n```\n"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    except Exception:
        pass  # fail-soft: never break session close


# --------------------------------------------------------------------------- #
# Path helpers
# --------------------------------------------------------------------------- #
def _norm(p: str) -> str:
    return p.replace("\\", "/").strip("/")


def path_under_any(path: str, directories: List[str], project_root: Path) -> bool:
    """True if ``path`` is inside any of ``directories`` (relative to project root)."""
    if not path:
        return False
    try:
        abs_path = Path(path)
        if not abs_path.is_absolute():
            abs_path = (project_root / path)
        abs_path = abs_path.resolve()
    except Exception:
        abs_path = None

    norm_path = _norm(path)
    for d in directories or []:
        nd = _norm(d)
        if not nd:
            continue
        # relative-string match
        if norm_path == nd or norm_path.startswith(nd + "/"):
            return True
        # absolute containment match
        if abs_path is not None:
            try:
                base = (project_root / d).resolve()
                abs_path.relative_to(base)
                return True
            except Exception:
                pass
    return False


def collect_touched_paths(event: Dict[str, Any]) -> List[str]:
    """Extract every file path touched by an Edit/Write/MultiEdit tool call."""
    paths: List[str] = []
    tool_input = event.get("tool_input") or {}
    if isinstance(tool_input, dict):
        fp = tool_input.get("file_path")
        if isinstance(fp, str):
            paths.append(fp)
        edits = tool_input.get("edits")
        if isinstance(edits, list):
            for e in edits:
                if isinstance(e, dict) and isinstance(e.get("file_path"), str):
                    paths.append(e["file_path"])
    return paths


# --------------------------------------------------------------------------- #
# Loop detection (v14 section 15.4)
# --------------------------------------------------------------------------- #
def tool_signature(event: Dict[str, Any]) -> Tuple[str, str]:
    """Return (stable signature, tool name) for a tool call.

    The signature hashes the tool name together with its fully-normalised input,
    so "the same call again" is judged on arguments, not just on the tool.
    """
    name = str(event.get("tool_name") or "")
    try:
        payload = json.dumps(event.get("tool_input"), sort_keys=True, default=str)
    except Exception:
        payload = repr(event.get("tool_input"))
    digest = hashlib.sha256(f"{name}\x00{payload}".encode("utf-8")).hexdigest()
    return digest[:16], name


def detect_loop(event: Dict[str, Any], config: Dict[str, Any],
                state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Record this tool call and report a loop the first time one trips.

    Returns a dict describing the loop, or ``None``. Advisory only -- the caller
    never blocks on it, matching this repo's "hooks nudge, they don't block" stance.
    """
    cfg = config.get("loop_detection") or {}
    if not cfg.get("enabled", True):
        return None

    threshold = cfg.get("repeat_threshold", DEFAULT_LOOP_THRESHOLD)
    try:
        threshold = max(2, int(threshold))
    except (TypeError, ValueError):
        threshold = DEFAULT_LOOP_THRESHOLD

    signature, tool_name = tool_signature(event)

    recent = state.get("recent_tool_calls")
    if not isinstance(recent, list):
        recent = []
    recent.append(signature)
    state["recent_tool_calls"] = recent[-LOOP_WINDOW:]

    # Length of the run of identical calls ending at this one.
    run = 0
    for previous in reversed(state["recent_tool_calls"]):
        if previous != signature:
            break
        run += 1

    if run < threshold:
        return None

    reported = state.get("loop_hits")
    if not isinstance(reported, list):
        reported = []
    if signature in reported:
        return None  # already flagged this exact call; stay quiet
    reported.append(signature)
    state["loop_hits"] = reported

    return {"signature": signature, "tool_name": tool_name, "repeat_count": run,
            "threshold": threshold}


def log_loop(project_root: Path, config: Dict[str, Any], event: Dict[str, Any],
             loop: Dict[str, Any]) -> None:
    """Append one JSON line to the loop-detection log. Fail-soft."""
    cfg = config.get("loop_detection") or {}
    rel = cfg.get("log_path") or DEFAULT_LOOP_LOG
    try:
        path = Path(rel)
        if not path.is_absolute():
            path = project_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "session_id": event.get("session_id"),
            "tool_name": loop["tool_name"],
            "signature": loop["signature"],
            "repeat_count": loop["repeat_count"],
            "threshold": loop["threshold"],
        }
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Output helpers
# --------------------------------------------------------------------------- #
def emit(obj: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(obj))
    sys.stdout.write("\n")


def session_context(event_name: str, additional_context: str,
                    session_title: Optional[str] = None,
                    reload_skills: bool = False) -> Dict[str, Any]:
    """Build a ``hookSpecificOutput`` envelope.

    ``reload_skills`` is a ``SessionStart``-only field: it asks Claude Code to
    re-scan the skill directories before the session begins. Live change
    detection does not watch a top-level skills directory that did not exist when
    the session started, which is how this repository once ran for months with
    skills that were never loaded. Setting it costs one directory scan and
    removes that failure mode.
    """
    hook_out: Dict[str, Any] = {
        "hookEventName": event_name,
        "additionalContext": additional_context,
    }
    out: Dict[str, Any] = {"hookSpecificOutput": hook_out}
    if session_title:
        out["hookSpecificOutput"]["sessionTitle"] = session_title
    if reload_skills:
        out["hookSpecificOutput"]["reloadSkills"] = True
    return out


# --------------------------------------------------------------------------- #
# Filesystem observation (Stop fallback)
# --------------------------------------------------------------------------- #
# `source_changed` and `ledger_touched` are set by PostToolUse, which only fires
# for Edit/Write/MultiEdit. A ledger appended by a shell redirect, or a source
# file rewritten by `sed -i`, is invisible to it -- so the reminder fires when
# the work *was* done, and stays silent when it wasn't.
#
# Claude Code's `FileChanged` event would be the right mechanism: it watches the
# disk and so sees writes from any process. Its matcher is a list of literal
# filenames, though, and our ledger filename rolls over every Monday -- a static
# watch list would go stale in a week, which is the failure already recorded in
# docs/RETROSPECTIVE.md. So: mtime, which does not care about filenames.
#
# Compared against `session_start_ts` rather than HEAD, because GUIDE section 7.3
# rejects `git diff` here on purpose: it would count pre-session changes, and the
# reminder is about work done *this* session.

DEFAULT_MTIME_SCAN_LIMIT = 2000
DEFAULT_MTIME_PRUNE = ("__pycache__", "node_modules", "dist", "build", "venv",
                       "site-packages", "target")


def current_ledger_path(config: Dict[str, Any], project_root: Path) -> Path:
    """Path to this ISO week's ledger file. One definition of the filename."""
    ledger_dir = project_root / ((config.get("ledger") or {}).get("directory")
                                 or "history")
    year, week, _ = datetime.date.today().isocalendar()
    return ledger_dir / f"{year}-W{week:02d}.md"


def changed_since(dirs: List[str], threshold: float, project_root: Path,
                  limit: int = DEFAULT_MTIME_SCAN_LIMIT,
                  prune: Any = ()) -> bool:
    """True if any file under ``dirs`` was modified after ``threshold``.

    Runs at every ``Stop``, so it is bounded in both directions: it returns on
    the *first* file newer than the threshold (cheap when something did change),
    and gives up after ``limit`` entries (predictable when nothing did). Hidden
    directories and the usual build/vendor trees are pruned.
    """
    skip = set(DEFAULT_MTIME_PRUNE) | {p for p in (prune or ()) if isinstance(p, str)}
    seen = 0
    for entry in dirs or []:
        root = Path(entry)
        if not root.is_absolute():
            root = project_root / entry
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if not d.startswith(".") and d not in skip]
            for name in filenames:
                if seen >= limit:
                    return False
                seen += 1
                try:
                    if (Path(dirpath) / name).stat().st_mtime > threshold:
                        return True
                except OSError:
                    continue
    return False


# --------------------------------------------------------------------------- #
# Tier-0 guard (PreToolUse)
# --------------------------------------------------------------------------- #
# Claude Code's `permissions.deny` is the stronger mechanism for anything a
# pattern can express, and it applies in every permission mode. It cannot
# express these four prohibitions: whether a push target is a *shared* branch is
# a fact about the repository, not about the command string, and a deny rule
# carries no exceptions -- one broad enough to stop `git push --force origin
# main` also stops the same push to your own topic branch. Hence a parser.
#
# Two decisions are emitted. `deny` where the prohibition is unambiguous, `ask`
# where the command is only *suspicious* and a human can settle it in one
# keystroke. `ask` still enforces: the call cannot proceed without a person.
#
# Every guard is a pure function over a token list so the parsing is testable
# without a repository (tests/test_hook.py::TestTier0Guard).

SHELL_TOOLS = ("Bash", "PowerShell")
DEFAULT_PROTECTED_ARCHIVE = "plans/archive"

# The separators Claude Code's own permission matcher recognises, longest first
# so `&&` is not split as two `&`. A rule must hold for every subcommand, so a
# prohibited call cannot hide behind a benign one.
_SUBCOMMAND_SPLIT = re.compile(r"&&|\|\||\|&|;|\||&|\n")

# `<<<` is a here-string; `<<WORD` a heredoc. `2 << 3` is a left shift, so a
# digit after the operator is deliberately excluded.
_HEREDOC = re.compile(r"<<<|<<-?[ \t]*(?![0-9])['\"\w]")

# `-F -`, `--file=-`, `-F /dev/stdin`: a commit message read from stdin.
_STDIN_FILE = re.compile(r"(?:^|\s)(?:-F|--file)[=\s]+(?:-|/dev/stdin)(?:\s|$)")

# git's own options that consume the following token, so the subcommand after
# them is not mistaken for their value (`git -C path push` is a push).
_GIT_VALUE_OPTS = ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path")

_REMOVAL_COMMANDS = ("rm", "remove-item", "ri", "rmdir", "del", "erase", "unlink")


def split_subcommands(command: str) -> List[str]:
    """Split a shell command on the separators the permission matcher uses.

    Deliberately naive about quoting: a separator inside a quoted string splits
    too. That over-reports rather than under-reports -- an extra fragment can
    only produce an extra check -- which is the safe direction for a guard.
    """
    return [part.strip() for part in _SUBCOMMAND_SPLIT.split(command or "")
            if part and part.strip()]


def _argv(subcommand: str) -> List[str]:
    return subcommand.split()


def _basename(token: str) -> str:
    # No str.removesuffix -- this file supports Python 3.8.
    name = Path(token).name.lower()
    return name[:-4] if name.endswith(".exe") else name


def git_subcommand(tokens: List[str]) -> Tuple[Optional[str], List[str]]:
    """Return ``(subcommand, args_after_it)`` for a git call, else ``(None, [])``."""
    if not tokens or _basename(tokens[0]) != "git":
        return None, []
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token in _GIT_VALUE_OPTS:
            i += 2
            continue
        if token.startswith("-"):
            i += 1
            continue
        return token, tokens[i + 1:]
    return None, []


def _positionals(args: List[str]) -> List[str]:
    return [a for a in args if not a.startswith("-")]


def refspec_destination(refspec: str) -> str:
    """`+HEAD:refs/heads/main` -> `main`; `main:feat/x` -> `feat/x`."""
    ref = refspec.lstrip("+").strip("'\"")
    if ":" in ref:
        ref = ref.split(":", 1)[1]
    if ref.startswith("refs/heads/"):
        ref = ref[len("refs/heads/"):]
    return ref


def guard_force_push(tokens: List[str], protected: Any,
                     current_branch: Any) -> Optional[Tuple[str, str]]:
    """Deny a force-push whose target resolves to a protected branch.

    ``protected`` and ``current_branch`` are callables so neither is resolved --
    both shell out to git -- until a force flag has actually been seen. This
    handler runs before every shell command; it must cost nothing on the
    overwhelming majority that are not pushes.
    """
    subcommand, args = git_subcommand(tokens)
    if subcommand != "push":
        return None

    positionals = _positionals(args)
    refspecs = positionals[1:]
    forced = (any(a == "-f" or a.startswith("--force") for a in args)
              or any(r.startswith("+") for r in refspecs))
    if not forced:
        return None

    protected_branches = protected()
    targets = [refspec_destination(r) for r in refspecs] or [current_branch()]
    hits = sorted({t for t in targets if t and t in protected_branches})
    if not hits:
        return None
    return "deny", (
        f"Tier-0 prohibition-force-push-shared: this force-pushes to "
        f"{', '.join('`' + h + '`' for h in hits)}, which this repository treats as "
        "shared. Push a new commit instead, or force-push a branch only you have. "
        "This prohibition is not overrideable."
    )


def guard_protected_paths(tokens: List[str],
                          protected_paths: List[str]) -> Optional[Tuple[str, str]]:
    """Deny a deletion aimed at the ledger or the plan archive."""
    if not tokens:
        return None

    head = _basename(tokens[0])
    if head == "git":
        subcommand, args = git_subcommand(tokens)
        if subcommand != "rm":
            return None
    elif head in _REMOVAL_COMMANDS:
        args = tokens[1:]
    else:
        return None

    for target in _positionals(args):
        cleaned = target.strip("'\"").replace("\\", "/").rstrip("*").rstrip("/")
        while cleaned.startswith("./"):
            cleaned = cleaned[2:]
        for guarded in protected_paths:
            guarded = guarded.rstrip("/")
            if guarded and (cleaned == guarded or cleaned.startswith(guarded + "/")):
                return "deny", (
                    f"Tier-0 prohibition-delete-ledger: `{target}` is inside "
                    f"`{guarded}`, the audit trail. Correct an entry by appending, "
                    "never by deleting. This prohibition is not overrideable."
                )
    return None


def guard_history_rewrite(tokens: List[str]) -> Optional[Tuple[str, str]]:
    """Escalate a history rewrite -- whether it is *published* is a runtime fact."""
    subcommand, args = git_subcommand(tokens)
    if subcommand is None:
        return None

    what = None
    if subcommand == "commit" and "--amend" in args:
        what = "amends the commit at HEAD"
    elif subcommand == "rebase" and not any(
            a in ("--abort", "--continue", "--skip", "--quit") for a in args):
        what = "rebases"
    elif subcommand == "reset" and "--hard" in args:
        what = "hard-resets"
    elif subcommand == "filter-branch":
        what = "rewrites history wholesale"

    if what is None:
        return None
    return "ask", (
        f"Tier-0 prohibition-rewrite-published-history: this {what}. Whether those "
        "commits are already pushed is not visible from the command, so this needs "
        "your call. If they are published, prefer a forward-fixing commit."
    )


def guard_heredoc(tokens: List[str], subcommand_text: str) -> Optional[Tuple[str, str]]:
    """Escalate stdin-fed programs and messages, and the editor-opening bare commit.

    Caveat observed 2026-08-06, not a defect in this function: an `ask` returned
    here is not guaranteed to reach a human. In a session with no one to prompt,
    the same registration that *blocked* a `deny` let two `ask` commands run
    silently. `deny` is self-resolving; `ask` depends on the session. See ROADMAP.
    """
    if _HEREDOC.search(subcommand_text):
        return "ask", (
            "rule-no-heredoc-stdin: this feeds a heredoc to a command. Shell and tool "
            "layers mangle escape sequences silently (docs/RETROSPECTIVE.md). Write the "
            "script to a file and run the file."
        )
    if _STDIN_FILE.search(subcommand_text):
        return "ask", (
            "rule-no-heredoc-stdin: this reads a message from stdin. Use "
            "`git commit -m` or `git commit -F <file>` -- never `-F -`."
        )

    name, args = git_subcommand(tokens)
    if name == "commit" and not any(
            a.startswith(("-m", "--message", "-F", "--file", "-C", "--reuse-message",
                          "--no-edit", "--amend", "--fixup", "--squash", "-t",
                          "--template"))
            for a in args):
        return "ask", (
            "rule-no-heredoc-stdin: a bare `git commit` opens an editor and can hang "
            "the session. Pass `-m` or `-F <file>`."
        )
    return None


class _GitContext:
    """Lazily-resolved repository facts. Nothing here runs until a guard asks."""

    def __init__(self, config: Dict[str, Any], project_root: Path,
                 extra_branches: List[str]) -> None:
        self._config = config
        self._root = project_root
        self._extra = extra_branches
        self._protected: Optional[set] = None
        self._current: Optional[str] = None

    def protected_branches(self) -> set:
        if self._protected is None:
            names = {resolve_main_branch(self._config, self._root)}
            names.update(b for b in self._extra if isinstance(b, str))
            self._protected = {n.strip() for n in names if n and n.strip()}
        return self._protected

    def current_branch(self) -> str:
        if self._current is None:
            self._current = _git(self._root, "rev-parse", "--abbrev-ref", "HEAD") or ""
        return self._current


def evaluate_tier0_guards(command: str, config: Dict[str, Any],
                          project_root: Path) -> Optional[Tuple[str, str]]:
    """Return the strongest ``(decision, reason)`` across every subcommand.

    A ``deny`` anywhere outranks an ``ask`` anywhere, so a prohibited call cannot
    be softened by pairing it with a merely suspicious one.
    """
    guard_cfg = config.get("tier0_guard") or {}
    if not guard_cfg.get("enabled", True):
        return None

    ledger_dir = (config.get("ledger") or {}).get("directory", "history")
    protected_paths = guard_cfg.get("protected_paths")
    if not isinstance(protected_paths, list) or not protected_paths:
        protected_paths = [ledger_dir, DEFAULT_PROTECTED_ARCHIVE]

    ctx = _GitContext(config, project_root,
                      guard_cfg.get("protected_branches") or [])

    findings: List[Tuple[str, str]] = []
    for subcommand in split_subcommands(command):
        tokens = _argv(subcommand)
        candidates = [
            guard_force_push(tokens, ctx.protected_branches, ctx.current_branch),
            guard_protected_paths(tokens, protected_paths),
        ]
        if guard_cfg.get("escalate_history_rewrite", True):
            candidates.append(guard_history_rewrite(tokens))
        if guard_cfg.get("escalate_heredoc", True):
            candidates.append(guard_heredoc(tokens, subcommand))
        findings.extend(c for c in candidates if c)

    for decision in ("deny", "ask"):
        for finding in findings:
            if finding[0] == decision:
                return finding
    return None


def permission_decision(decision: str, reason: str) -> Dict[str, Any]:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}


# --------------------------------------------------------------------------- #
# Handlers
# --------------------------------------------------------------------------- #
def run_env_checks(config: Dict[str, Any], project_root: Path) -> List[str]:
    lines: List[str] = []
    tool_paths = (config.get("env_check") or {}).get("tool_paths") or {}
    for name, spec in tool_paths.items():
        if not isinstance(spec, dict):
            continue
        raw_path = spec.get("path", "")
        tool_path = Path(raw_path)
        if not tool_path.is_absolute():
            tool_path = (project_root / raw_path)
        version_flag = spec.get("version_flag", "--version")

        if version_flag in (None, ""):
            exists = tool_path.exists() or _which(raw_path) is not None
            lines.append(f"  - {name}: {'found' if exists else 'NOT FOUND'} ({raw_path})")
            continue

        try:
            res = subprocess.run(
                [str(raw_path), str(version_flag)],
                capture_output=True, text=True, timeout=15,
            )
            ver = (res.stdout or res.stderr or "").strip().splitlines()
            ver_str = ver[0] if ver else "(no output)"
            lines.append(f"  - {name}: {ver_str}")
        except Exception:
            lines.append(f"  - {name}: NOT FOUND ({raw_path})")
    return lines


def api_key_warning() -> Optional[str]:
    """Warn when ANTHROPIC_API_KEY is set.

    Claude Code prefers an ``ANTHROPIC_API_KEY`` in the environment over the
    signed-in Claude subscription, so a stray key silently moves billing onto
    per-token API charges. Legitimate for API users -- hence a warning, never a
    failure. See docs/governance-integration-decision.md section 2.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    return ("⚠️ ANTHROPIC_API_KEY is set — Claude Code will authenticate with that key "
            "instead of your Claude subscription, and usage bills per token. Unset it "
            "to use the subscription.")


def _which(cmd: str) -> Optional[str]:
    from shutil import which
    try:
        return which(cmd)
    except Exception:
        return None


def parse_next_action(config: Dict[str, Any], project_root: Path) -> Optional[str]:
    roadmap_rel = config.get("roadmap_file")
    if not roadmap_rel:
        return None
    roadmap = project_root / roadmap_rel
    # Require the marker at the start of the line (after optional whitespace,
    # blockquote '>' or a list bullet) so prose that merely *mentions* the
    # marker inline doesn't produce a false match.
    marker = re.compile(r"^\s*(?:[>]\s*)?(?:[-*+]\s+)?\*\*Next action:\*\*\s*(.+)$")
    try:
        for line in roadmap.read_text(encoding="utf-8").splitlines():
            m = marker.match(line)
            if m:
                return m.group(1).strip()
    except Exception:
        return None
    return None


def handle_session_start(event: Dict[str, Any], config: Dict[str, Any],
                         project_root: Path) -> None:
    purge_stale_state()
    session_id = event.get("session_id")
    save_state(session_id, default_state())

    parts: List[str] = ["## Adaptive Workflow — session start"]

    gs = git_status(project_root)
    if gs.get("branch"):
        git_line = f"Git: branch `{gs['branch']}`"
        if gs.get("dirty"):
            git_line += " (dirty working tree — F1: stash/commit before you begin?)"
        if gs.get("ahead") not in (None, "0") or gs.get("behind") not in (None, "0"):
            git_line += f" — ahead {gs.get('ahead')}, behind {gs.get('behind')}"
        parts.append(git_line)

    env_lines = run_env_checks(config, project_root)
    api_key_note = api_key_warning()
    if api_key_note:
        env_lines.append(f"  - {api_key_note}")
    if env_lines:
        parts.append("Environment (F2):\n" + "\n".join(env_lines))

    next_action = parse_next_action(config, project_root)
    if next_action:
        parts.append(f"Roadmap next action (F4): {next_action}")

    if has_outstanding_plan(project_root):
        parts.append("⚠️ Unfinished plan detected (plans/UNFINISHED.md) — "
                     "F4: surface it and ask whether to continue or archive.")

    update_notice = check_workflow_updates(config, project_root)
    if update_notice:
        parts.append(update_notice)

    parts.append("Reminders: log intentional changes to the weekly ledger "
                 "(history/YYYY-Www.md); add doc frontmatter (provenance + version) to new docs.")

    emit(session_context("SessionStart", "\n\n".join(parts),
                         session_title="Adaptive Workflow session",
                         reload_skills=skills_dir_exists(project_root)))


def handle_pre_tool_use(event: Dict[str, Any], config: Dict[str, Any],
                        project_root: Path) -> None:
    """Tier-0 guard. Silent unless a prohibition is implicated.

    Emitting nothing defers to the normal permission flow, which is the correct
    default -- returning ``allow`` here would auto-approve every shell command in
    the session. Deliberately does not touch the session state file: this runs
    before every Bash and PowerShell call, and the churn would be constant.
    """
    if event.get("tool_name") not in SHELL_TOOLS:
        return

    tool_input = event.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not command.strip():
        return

    finding = evaluate_tier0_guards(command, config, project_root)
    if finding:
        emit(permission_decision(*finding))


def handle_post_tool_use(event: Dict[str, Any], config: Dict[str, Any],
                         project_root: Path) -> None:
    session_id = event.get("session_id")
    state = load_state(session_id)

    paths = collect_touched_paths(event)
    source_dirs = config.get("source_directories") or []
    doc_dirs = config.get("documentation_directories") or []
    ledger_dir = (config.get("ledger") or {}).get("directory", "history")

    doc_touched_now = False
    for p in paths:
        if path_under_any(p, source_dirs, project_root):
            state["source_changed"] = True
        if path_under_any(p, [ledger_dir], project_root):
            state["ledger_touched"] = True
        if path_under_any(p, doc_dirs, project_root):
            doc_touched_now = True

    notes: List[str] = []
    if (state.get("source_changed") and not doc_touched_now
            and not state.get("doc_nudged")):
        state["doc_nudged"] = True
        notes.append("Consider updating docs and the weekly ledger "
                     "(history/YYYY-Www.md) if this change is worth tracing.")

    # Skills fail silently in every direction: a misplaced directory loads
    # nothing, an unknown frontmatter key is ignored, and a body past the
    # compaction budget is truncated without a diagnostic. Nothing reports any of
    # it, so the one moment worth spending a nudge on is just after a skill file
    # is written. Advisory only -- PostToolUse fires after the write.
    if (any(path_under_any(p, [".claude/skills"], project_root) for p in paths)
            and not state.get("skill_nudged")):
        state["skill_nudged"] = True
        notes.append(
            "Skill file edited. The `skill-authoring` skill has the rules "
            "(500-line / ~5,000-token caps, documented frontmatter keys only); "
            "`claude-code-layout` has the placement rules. Run "
            "`python -m unittest tests.test_skills tests.test_claude_layout`, and "
            "mirror `.claude/skills/` into `templates/skills/` in the same commit."
        )

    loop = detect_loop(event, config, state)
    if loop:
        log_loop(project_root, config, event, loop)
        notes.append(
            f"Loop check: `{loop['tool_name'] or 'this tool'}` has now been called "
            f"{loop['repeat_count']}x in a row with identical arguments. If it isn't "
            "making progress, change the approach rather than retrying — vary the "
            "arguments, read the error, or ask the user."
        )

    save_state(session_id, state)

    if notes:
        emit(session_context("PostToolUse", "\n\n".join(notes)))


def handle_stop(event: Dict[str, Any], config: Dict[str, Any],
                project_root: Path) -> None:
    session_id = event.get("session_id")
    state = load_state(session_id)

    max_blocks = (config.get("stop_hook") or {}).get("max_blocks", DEFAULT_MAX_BLOCKS)

    if event.get("stop_hook_active") or state.get("stop_block_count", 0) >= max_blocks:
        return  # exit 0, no output

    # Resolved after the short-circuit so a capped/re-entrant Stop costs no git calls.
    cached_main = state.get("main_branch_detected")
    main_branch = resolve_main_branch(config, project_root, state)
    if state.get("main_branch_detected") != cached_main:
        save_state(session_id, state)  # persist the probe even if we don't block

    # The PostToolUse flags are the fast path; mtime is the fallback that sees
    # work done by any other means. Flag first, so the cheap answer wins.
    stop_cfg = config.get("stop_hook") or {}
    source_changed = bool(state.get("source_changed"))
    ledger_touched = bool(state.get("ledger_touched"))

    if stop_cfg.get("mtime_fallback", True):
        since = state.get("session_start_ts") or 0.0
        if not ledger_touched:
            try:
                ledger = current_ledger_path(config, project_root)
                ledger_touched = (ledger.is_file()
                                  and ledger.stat().st_mtime > since)
            except OSError:
                pass
        if not source_changed:
            source_changed = changed_since(
                config.get("source_directories") or [], since, project_root,
                limit=stop_cfg.get("mtime_scan_limit", DEFAULT_MTIME_SCAN_LIMIT),
                prune=stop_cfg.get("mtime_prune") or (),
            )

    reminders: List[str] = []

    gs = git_status(project_root)
    # Our own breadcrumb does not make the tree dirty -- otherwise writing it
    # guarantees the next Stop fires again, forever. This only ever *clears* a
    # false positive: git_status stays the authority on whether work exists.
    if gs.get("dirty") and not dirty_excluding_breadcrumb(project_root):
        gs["dirty"] = False
    if gs.get("dirty") and gs.get("branch") and gs.get("branch") != main_branch:
        reminders.append(
            f"Working tree is dirty on branch `{gs['branch']}`. "
            "Phase 3 closure: commit & push before ending "
            "(`git add -A && git commit -m \"<msg>\" && git push`; avoid a bare "
            "`git commit`, which can open an editor and hang, and avoid heredocs "
            "/ `-F -`)."
        )

    if source_changed and not ledger_touched:
        reminders.append(
            "Source files changed this session but the weekly ledger "
            "(history/YYYY-Www.md) wasn't updated. Add an entry "
            "(What / Why / Refs) before closing."
        )

    loop_hits = state.get("loop_hits") or []
    if loop_hits:
        reminders.append(
            f"Loop detection fired {len(loop_hits)}x this session (repeated identical "
            "tool calls). If any of those retries masked a real problem, note it in "
            "docs/RETROSPECTIVE.md — a mistake recorded twice becomes a permanent rule."
        )

    # Durable safety net: any dirty tree at Stop leaves a breadcrumb (on any
    # branch, so main-branch closures are covered too). This happens whether or
    # not we block, so the record survives an ignored reminder or a force-close.
    if gs.get("dirty"):
        write_unfinished_breadcrumb(project_root, gs, reminders)

    if reminders:
        state["stop_block_count"] = state.get("stop_block_count", 0) + 1
        save_state(session_id, state)
        emit({"decision": "block", "reason": "\n".join(reminders)})
    # else: exit 0 silently, allowing the session to end.


HANDLERS = {
    "SessionStart": handle_session_start,
    "PreToolUse": handle_pre_tool_use,
    "PostToolUse": handle_post_tool_use,
    "Stop": handle_stop,
}


# --------------------------------------------------------------------------- #
# --self-test: config validation + governance maturity report
# --------------------------------------------------------------------------- #
def validate_against_schema(instance: Any, schema: Dict[str, Any],
                            path: str = "") -> List[str]:
    """Validate ``instance`` against the subset of JSON Schema this repo uses.

    Supports: type, properties, additionalProperties (bool), required, enum,
    minimum, items. Deliberately not a general implementation -- it exists so
    ``--self-test`` needs no third-party ``jsonschema`` dependency.
    """
    errors: List[str] = []
    where = path or "<root>"

    types = schema.get("type")
    if types:
        wanted = types if isinstance(types, list) else [types]
        ok = any(
            (t == "object" and isinstance(instance, dict))
            or (t == "array" and isinstance(instance, list))
            or (t == "string" and isinstance(instance, str))
            or (t == "boolean" and isinstance(instance, bool))
            or (t == "integer" and isinstance(instance, int) and not isinstance(instance, bool))
            or (t == "number" and isinstance(instance, (int, float)) and not isinstance(instance, bool))
            or (t == "null" and instance is None)
            for t in wanted
        )
        if not ok:
            errors.append(f"{where}: expected {'/'.join(wanted)}, got {type(instance).__name__}")
            return errors  # cascading checks would just add noise

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{where}: {instance!r} is not one of {schema['enum']}")

    if "minimum" in schema and isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if instance < schema["minimum"]:
            errors.append(f"{where}: {instance} is below the minimum {schema['minimum']}")

    if isinstance(instance, dict):
        props = schema.get("properties") or {}
        for key in schema.get("required") or []:
            if key not in instance:
                errors.append(f"{where}: missing required key '{key}'")
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props:
                    errors.append(f"{where}: unknown key '{key}'")
        for key, value in instance.items():
            if key in props:
                errors += validate_against_schema(value, props[key], f"{where}.{key}")
            elif isinstance(schema.get("additionalProperties"), dict):
                errors += validate_against_schema(
                    value, schema["additionalProperties"], f"{where}.{key}")

    if isinstance(instance, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(instance):
            errors += validate_against_schema(item, schema["items"], f"{where}[{i}]")

    return errors


def _has_frontmatter(path: Path) -> bool:
    try:
        with path.open(encoding="utf-8") as fh:
            return fh.readline().strip() == "---"
    except Exception:
        return False


def _declares_exclusion(path: Path) -> bool:
    """True if the doc's own frontmatter opts out with ``exclude_from_ai: true``."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return False
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, _, value = line.partition(":")
        if key.strip() == "exclude_from_ai" and value.strip().lower() == "true":
            return True
    return False


def is_excluded_doc(path: Path, config: Dict[str, Any], project_root: Path) -> bool:
    """Single decision point for "is this doc held to the frontmatter rule?".

    Three inputs, deliberately not one:

    * ``.prov.md`` sidecars *are* the provenance mechanism for formats that
      cannot carry frontmatter (GUIDE section 6.2); demanding it of them is
      circular.
    * ``documentation_exclude`` covers paths whose *defect is the missing
      frontmatter* -- a staging or vendored tree. An in-file opt-out cannot
      reach those, because reading it would require the frontmatter they lack.
    * ``exclude_from_ai: true`` covers a doc that has frontmatter and still
      wants out of context assembly, such as a sibling CHANGELOG (GUIDE 6.4).
    """
    if path.name.endswith(".prov.md"):
        return True
    try:
        rel = path.resolve().relative_to(project_root.resolve()).as_posix()
    except Exception:
        rel = path.as_posix()
    for prefix in config.get("documentation_exclude") or []:
        if not isinstance(prefix, str) or not prefix:
            continue
        clean = prefix.replace("\\", "/").strip("/")
        if rel == clean or rel.startswith(clean + "/"):
            return True
    return _declares_exclusion(path)


# --------------------------------------------------------------------------- #
# Source confidence (Golden Rule Research Protocol)
# --------------------------------------------------------------------------- #
# A checklist item's confidence is DERIVED from its own source fields, never
# asserted by hand -- the same discipline `enforcement_mode` follows, and for
# the same reason: a number nobody can recompute drifts.
#
# The protocol's determination table is a ladder of *thresholds*, not exact
# keys: "authority >= 10 and consensus >= 3 and age > 5 years" means (10, 4, 6)
# is also level 5. Ordered strongest-first; the first row that fits wins.
#
# Percentage ranges from the source table are deliberately not modelled. No
# procedure distinguishes 94% from 96%, so the level survives and the false
# precision does not.

#                     authority, consensus, age_days,     level
CONFIDENCE_MATRIX = [
    (10, 3, 5 * 365, 5),   # Industry Standard  -- IETF/W3C/ISO/IEEE
    (8,  2, 3 * 365, 4),   # Enterprise-Proven  -- NIST/OWASP/vendor docs
    (6,  1, 365,     3),   # Community-Validated
    (4,  1, 0,       2),   # Emerging
]
CONFIDENCE_FLOOR = 1       # Uncertain -- no authoritative source found


def derive_confidence(source_authority: Any, source_consensus: Any,
                      age_days: Any) -> int:
    """Return the confidence level 1-5 implied by an item's own source fields.

    Strictly a function of its arguments so the test and the runtime cannot
    disagree. Non-numeric input yields the floor rather than raising: a
    malformed item is uncertain, not fatal.
    """
    try:
        authority = int(source_authority)
        consensus = int(source_consensus)
        age = float(age_days)
    except (TypeError, ValueError):
        return CONFIDENCE_FLOOR
    for min_authority, min_consensus, min_age, level in CONFIDENCE_MATRIX:
        if authority >= min_authority and consensus >= min_consensus and age > min_age:
            return level
    return CONFIDENCE_FLOOR


def _outstanding_recurrences(retro: Path) -> List[str]:
    """Entries marked '(recurring)' that carry no '**Codified:**' line.

    These are the mistakes the self-hardening loop still owes a rule file.
    """
    try:
        text = retro.read_text(encoding="utf-8")
    except Exception:
        return []
    outstanding: List[str] = []
    sections = re.split(r"^### ", text, flags=re.MULTILINE)[1:]
    for section in sections:
        heading = section.splitlines()[0].strip()
        if "(recurring)" in heading.lower() and "**codified:**" not in section.lower():
            outstanding.append(heading)
    return outstanding


def _print_report(lines: List[str]) -> None:
    """Print the report, degrading gracefully on a non-UTF-8 console.

    Windows terminals commonly default to cp1252, which cannot encode the emoji
    used in the API-key warning. Rather than crash or emit mojibake, fall back to
    ASCII when the active encoding cannot take it.
    """
    text = "\n".join(lines)
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
    except (UnicodeEncodeError, LookupError):
        text = text.encode("ascii", "replace").decode("ascii")
    print(text)


def run_self_test() -> int:
    """Validate the config and report workflow health.

    Exit code reflects *validation* only; the health checks are reported, never
    enforced -- a young repository is not a broken one.

    This function **must not write anything**. It reports on the repository; an
    instrument that mutates what it measures is not one. The maturity ladder and
    its tracker file were removed on 2026-08-29 for exactly that reason, and
    `test_hook.TestSelfTest.test_self_test_does_not_write_to_the_repository`
    holds this property by comparing the file tree before and after.
    """
    out: List[str] = ["Adaptive Workflow -- self-test", "=" * 60]
    failures: List[str] = []

    config_path = find_config_path()
    if config_path is None:
        _print_report(out + ["", "FAIL: no workflow_config.json found."])
        return 1
    out.append(f"config: {config_path}")

    config, project_root = load_config()
    if not config:
        _print_report(out + ["", f"FAIL: {config_path} is empty or unparseable."])
        return 1
    out.append(f"root:   {project_root}")
    out.append("")

    checks: Dict[str, bool] = {"config_parses": True}

    # --- schema validation ---------------------------------------------------
    schema_path = find_schema_path()
    if schema_path is not None:
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            errors = validate_against_schema(config, schema)
        except Exception as exc:                       # noqa: BLE001 - reported below
            errors = [f"schema unreadable: {exc}"]
        if errors:
            failures += errors
            out.append("[FAIL] config schema validation")
            out += [f"         {e}" for e in errors]
        else:
            out.append("[ ok ] config valid against schemas/config_schema.json")
        checks["config_valid"] = not errors
    else:
        out.append("[warn] schemas/config_schema.json not found — validation skipped")
        checks["config_valid"] = False

    # --- ledger currency -----------------------------------------------------
    ledger_file = current_ledger_path(config, project_root)
    checks["ledger_current"] = ledger_file.is_file()
    out.append(f"[{' ok ' if checks['ledger_current'] else 'warn'}] weekly ledger "
               f"{ledger_file.relative_to(project_root) if ledger_file.is_file() else ledger_file.name}"
               f"{'' if checks['ledger_current'] else ' - not created yet'}")

    # --- unfinished plan -----------------------------------------------------
    checks["no_unfinished"] = not has_outstanding_plan(project_root)
    breadcrumb_only = ((project_root / BREADCRUMB_PATH).is_file()
                       and checks["no_unfinished"])
    out.append(f"[{' ok ' if checks['no_unfinished'] else 'warn'}] plans/UNFINISHED.md "
               f"{'absent' if not (project_root / BREADCRUMB_PATH).is_file() else ('auto-breadcrumb only - not a plan owed' if breadcrumb_only else 'PRESENT - surface it (F4)')}")

    # --- loop detection ------------------------------------------------------
    checks["loop_detection"] = bool((config.get("loop_detection") or {}).get("enabled", True))
    out.append(f"[{' ok ' if checks['loop_detection'] else 'warn'}] loop detection "
               f"{'enabled' if checks['loop_detection'] else 'disabled'}")

    # --- documentation frontmatter -------------------------------------------
    missing_fm: List[str] = []
    for doc_dir in config.get("documentation_directories") or []:
        base = project_root / doc_dir
        if not base.is_dir():
            continue
        for md in sorted(base.rglob("*.md")):
            if is_excluded_doc(md, config, project_root):
                continue
            if not _has_frontmatter(md):
                missing_fm.append(str(md.relative_to(project_root)))
    checks["docs_have_frontmatter"] = not missing_fm
    if missing_fm:
        out.append(f"[warn] {len(missing_fm)} doc(s) without frontmatter:")
        out += [f"         {p}" for p in missing_fm[:10]]
        if len(missing_fm) > 10:
            out.append(f"         ... and {len(missing_fm) - 10} more")
    else:
        out.append("[ ok ] every doc carries frontmatter")

    gov = config.get("governance") or {}
    library_root = project_root / (gov.get("library_root") or DEFAULT_LIBRARY_ROOT)

    # --- checklist source revalidation ---------------------------------------
    # A cited standard moves on whether or not anyone re-reads it. Rather than
    # tracking each source's version -- a hand-maintained file that itself goes
    # stale silently -- this warns on age alone, uniformly and offline. The item
    # carries `source_version`, so clearing a warning is one lookup.
    interval = config.get("revalidation_interval_days", 180)
    stale: List[str] = []
    # Count what was actually examined. Without this, an empty or missing
    # `05-domains/` leaves `stale` empty and the branch below reports
    # "[ ok ] checklist sources validated" -- a pass earned by checking nothing.
    # Observed on 2026-08-29: with `.ai/` deleted entirely, --self-test still
    # printed the ok line and still exited 0. A check that cannot distinguish
    # "all clear" from "no corpus" is worse than no check, because it actively
    # asserts the thing it failed to look at.
    examined = 0
    if interval:
        cutoff = datetime.date.today() - datetime.timedelta(days=int(interval))
        for rule_path in sorted((library_root / "05-domains").glob("rule-*.json")):
            try:
                rule = json.loads(rule_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            for entry in rule.get("checklist") or []:
                try:
                    validated = datetime.date.fromisoformat(entry["last_validated"])
                except Exception:
                    continue
                examined += 1
                if validated < cutoff:
                    stale.append(f"{entry.get('id')} ({entry.get('source_version')}, "
                                 f"last validated {validated})")
    checks["sources_current"] = bool(examined) and not stale
    if stale:
        out.append(f"[warn] {len(stale)} checklist item(s) due revalidation "
                   f"(>{interval}d):")
        out += [f"         {s}" for s in stale[:10]]
        if len(stale) > 10:
            out.append(f"         ... and {len(stale) - 10} more")
    elif interval and examined:
        out.append(f"[ ok ] checklist sources validated within {interval}d "
                   f"({examined} items)")
    elif interval:
        out.append(f"[warn] no checklist items found under "
                   f"{(library_root / '05-domains').name}/ -- nothing was revalidated")

    # --- skill verification stamps -------------------------------------------
    # Same argument as above, applied to claims about Claude Code itself, which
    # ships several times a week. `tests/test_skills.py::VerificationStamps`
    # enforces that the stamp exists and is well-formed; only *age* is judged
    # here, because a date going quietly out of range is not a build failure --
    # it is a prompt to re-read the docs. Reported, never enforced.
    stale_stamps: List[str] = []
    skills_root = project_root / ".claude" / "skills"
    if interval and skills_root.is_dir():
        cutoff = datetime.date.today() - datetime.timedelta(days=int(interval))
        for md in sorted(skills_root.rglob("*.md")):
            try:
                text = md.read_text(encoding="utf-8")
            except OSError:
                continue
            match = STAMP_RE.search(text)
            if not match:
                continue
            try:
                stamped = datetime.date.fromisoformat(match.group(1))
            except ValueError:
                continue
            if stamped < cutoff:
                rel = md.relative_to(project_root).as_posix()
                stale_stamps.append(f"{rel} (v{match.group(2)}, stamped {stamped})")
    checks["skill_stamps_current"] = not stale_stamps
    if stale_stamps:
        out.append(f"[warn] {len(stale_stamps)} skill file(s) due re-verification "
                   f"(>{interval}d):")
        out += [f"         {s}" for s in stale_stamps[:10]]
        if len(stale_stamps) > 10:
            out.append(f"         ... and {len(stale_stamps) - 10} more")
        out.append("         Refresh per `.claude/skills/skill-authoring/SKILL.md`: "
                   "read the highest installed version, diff the release notes, "
                   "re-read each cited page in full.")
    elif interval and skills_root.is_dir():
        out.append(f"[ ok ] skill verification stamps within {interval}d")

    # --- tier-0 prohibitions --------------------------------------------------
    prohibitions = sorted((library_root / "02-market-rules" / "prohibitions").glob("prohibition-*.json"))
    checks["prohibitions_present"] = bool(prohibitions)
    out.append(f"[{' ok ' if prohibitions else 'warn'}] tier-0 prohibitions: "
               f"{len(prohibitions)} defined")

    # --- retrospective --------------------------------------------------------
    retro_rel = config.get("retrospective_file")
    retro = project_root / retro_rel if retro_rel else None
    has_entry = bool(retro and retro.is_file() and re.search(r"^### ", retro.read_text(
        encoding="utf-8", errors="replace"), flags=re.MULTILINE))
    checks["retrospective_active"] = has_entry
    out.append(f"[{' ok ' if has_entry else 'warn'}] retrospective "
               f"{'has entries' if has_entry else 'empty or not configured'}")

    outstanding = _outstanding_recurrences(retro) if retro and retro.is_file() else []
    checks["recurrences_codified"] = not outstanding
    if outstanding:
        out.append(f"[warn] {len(outstanding)} recurring mistake(s) not yet codified into a rule:")
        out += [f"         {h}" for h in outstanding]

    # --- environment ----------------------------------------------------------
    warning = api_key_warning()
    if warning:
        out += ["", warning]
    out.append("")
    env_lines = run_env_checks(config, project_root)
    if env_lines:
        out.append("Environment:")
        out += env_lines
        # Printed rather than probed: `claude` is not on PATH under the VS Code
        # extension, and an env_check that always fails trains the reader to skip
        # the whole block (docs/RETROSPECTIVE.md, 2026-08-04). The second line
        # exists because two sessions here recorded the version as unobtainable
        # before anyone looked at the install path, where it had been all along.
        out.append("  note: the `opus` alias resolves to Opus 5 only on Claude Code v2.1.219+")
        out.append("  note: no `claude` on PATH? the VS Code extension directory name "
                   "carries the version (~/.vscode/extensions/anthropic.claude-code-*)")

    # The governance maturity ladder (levels 1-5) and its `maturity-tracker.json`
    # were removed 2026-08-29. Two reasons, both observed rather than argued:
    #
    # 1. The tracker rewrote a *tracked* file on every `--self-test`, so merely
    #    running the suite dirtied the working tree. It was reverted by hand
    #    three times in one session before anyone named it as the problem. A
    #    health check that mutates the repo it is reporting on is an instrument
    #    that manufactures the state it measures.
    # 2. The level was "reported, never enforced" by design -- a number nothing
    #    consumed. It read as a score, and a score invites optimising the score.
    #
    # The individual `checks` above still print. What is gone is the ladder that
    # summed them into a grade and the file that stored it.

    if failures:
        out += ["", f"RESULT: FAIL - {len(failures)} validation error(s)."]
        _print_report(out)
        return 1

    out += ["", "RESULT: PASS - configuration is valid."]
    _print_report(out)
    return 0


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if "--self-test" in argv:
        # Runs standalone: reads no stdin, and is the one path allowed to exit
        # non-zero, because it is invoked by a human or CI, never by a hook event.
        try:
            return run_self_test()
        except Exception as exc:                       # noqa: BLE001 - surfaced to the caller
            print(f"self-test crashed: {exc}", file=sys.stderr)
            return 1

    dry_run = "--dry-run" in argv

    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # fail-soft: unparseable input never breaks the session

    if not isinstance(event, dict):
        return 0

    event_name = event.get("hookEventName") or event.get("hook_event_name")
    handler = HANDLERS.get(event_name)
    if handler is None:
        return 0

    try:
        config, project_root = load_config()
    except Exception:
        config, project_root = {}, Path(".").resolve()

    if dry_run:
        # In dry-run mode we still compute output but suppress state mutation by
        # routing writes to a throwaway session id.
        event = dict(event)
        event["session_id"] = None

    try:
        handler(event, config, project_root)
    except Exception:
        return 0  # fail-soft: any handler error is swallowed

    return 0


if __name__ == "__main__":
    sys.exit(main())
