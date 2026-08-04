#!/usr/bin/env python3
"""Adaptive Self-Correcting Workflow -- hook dispatcher.

A single fail-soft dispatcher invoked by Claude Code for the ``SessionStart``,
``PostToolUse`` and ``Stop`` hook events. It reads the event JSON from stdin,
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
from pathlib import Path
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
DEFAULT_MATURITY_TRACKER = ".ai/00-system/maturity-tracker.json"


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
                    session_title: Optional[str] = None) -> Dict[str, Any]:
    hook_out: Dict[str, Any] = {
        "hookEventName": event_name,
        "additionalContext": additional_context,
    }
    out: Dict[str, Any] = {"hookSpecificOutput": hook_out}
    if session_title:
        out["hookSpecificOutput"]["sessionTitle"] = session_title
    return out


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

    unfinished = project_root / "plans" / "UNFINISHED.md"
    if unfinished.is_file():
        parts.append("⚠️ Unfinished plan detected (plans/UNFINISHED.md) — "
                     "F4: surface it and ask whether to continue or archive.")

    update_notice = check_workflow_updates(config, project_root)
    if update_notice:
        parts.append(update_notice)

    parts.append("Reminders: log intentional changes to the weekly ledger "
                 "(history/YYYY-Www.md); add doc frontmatter (provenance + version) to new docs.")

    emit(session_context("SessionStart", "\n\n".join(parts),
                         session_title="Adaptive Workflow session"))


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

    reminders: List[str] = []

    gs = git_status(project_root)
    if gs.get("dirty") and gs.get("branch") and gs.get("branch") != main_branch:
        reminders.append(
            f"Working tree is dirty on branch `{gs['branch']}`. "
            "Phase 3 closure: commit & push before ending "
            "(`git add -A && git commit -m \"<msg>\" && git push`; avoid a bare "
            "`git commit`, which can open an editor and hang, and avoid heredocs "
            "/ `-F -`)."
        )

    if state.get("source_changed") and not state.get("ledger_touched"):
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
    """Validate the config, report workflow health, and derive a maturity level.

    Exit code reflects *validation* only. The maturity level is reported, never
    enforced -- a young repository is not a broken one.
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
    schema_path = Path(__file__).resolve().parent.parent / "schemas" / "config_schema.json"
    if schema_path.is_file():
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
    ledger_cfg = config.get("ledger") or {}
    ledger_dir = project_root / (ledger_cfg.get("directory") or "history")
    year, week, _ = datetime.date.today().isocalendar()
    ledger_file = ledger_dir / f"{year}-W{week:02d}.md"
    checks["ledger_current"] = ledger_file.is_file()
    out.append(f"[{' ok ' if checks['ledger_current'] else 'warn'}] weekly ledger "
               f"{ledger_file.relative_to(project_root) if ledger_file.is_file() else ledger_file.name}"
               f"{'' if checks['ledger_current'] else ' - not created yet'}")

    # --- unfinished plan -----------------------------------------------------
    unfinished = project_root / "plans" / "UNFINISHED.md"
    checks["no_unfinished"] = not unfinished.is_file()
    out.append(f"[{' ok ' if checks['no_unfinished'] else 'warn'}] plans/UNFINISHED.md "
               f"{'absent' if checks['no_unfinished'] else 'PRESENT - surface it (F4)'}")

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
            # `.prov.md` sidecars ARE the provenance mechanism for formats that
            # cannot carry frontmatter (GUIDE section 6.2) -- demanding frontmatter
            # on them would be circular.
            if md.name.endswith(".prov.md"):
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

    # --- tier-0 prohibitions --------------------------------------------------
    gov = config.get("governance") or {}
    library_root = project_root / (gov.get("library_root") or DEFAULT_LIBRARY_ROOT)
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
        out.append("  note: the `opus` alias resolves to Opus 5 only on Claude Code v2.1.219+")

    # --- maturity -------------------------------------------------------------
    levels = [
        (1, "Ad-hoc", ["config_parses"]),
        (2, "Repeatable", ["config_valid", "ledger_current"]),
        (3, "Defined", ["no_unfinished", "loop_detection", "docs_have_frontmatter"]),
        (4, "Managed", ["prohibitions_present", "retrospective_active"]),
        (5, "Optimized", ["recurrences_codified"]),
    ]
    level, name = 0, "Uninitialised"
    for value, label, required in levels:
        if all(checks.get(k) for k in required):
            level, name = value, label
        else:
            break

    out += ["", "-" * 60, f"Governance maturity: level {level}/5 ({name})",
            "  Reported, never enforced - see docs/governance-integration-decision.md"]

    tracker_rel = gov.get("maturity_tracker") or DEFAULT_MATURITY_TRACKER
    tracker = project_root / tracker_rel
    try:
        tracker.parent.mkdir(parents=True, exist_ok=True)
        tracker.write_text(json.dumps({
            "maturity_level": level,
            "maturity_name": name,
            "note": "Regenerated by `python hooks/workflow_hook.py --self-test`. "
                    "Reported, never enforced.",
            "last_assessment": datetime.date.today().isoformat(),
            "checks": checks,
            "outstanding_recurrences": outstanding,
        }, indent=2) + "\n", encoding="utf-8")
        out.append(f"  written to {tracker_rel}")
    except Exception as exc:                           # noqa: BLE001 - non-fatal
        out.append(f"  (could not write {tracker_rel}: {exc})")

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
