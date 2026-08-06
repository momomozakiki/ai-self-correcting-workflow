#!/usr/bin/env python3
"""Layout tests for ``.claude/`` -- does Claude Code actually read what is here?

Stdlib ``unittest`` only -- run with::

    python -m unittest discover -s tests
    # or
    python -m unittest tests.test_claude_layout

``tests/test_skills.py`` checks that a skill is *well formed*. This module checks
that configuration is *in a place something reads*, which is a different question
and the one this repository keeps getting wrong:

* skills sat in a repo-root ``skills/`` directory for months, discovered by
  nothing (fixed 2026-08-06);
* ``templates/settings.json.hooks`` -- what adopters merge -- shipped with no
  ``PreToolUse`` block, so every adopting project ran with four Tier-0
  prohibitions documented as ``live`` and nothing enforcing them;
* ``.claude/settings.local.json`` was ignored only by a machine-global git rule
  that no clone inherits.

None of the three produced an error, and the suite was green through all of them.
That is the defect class: **correct content that nothing consumes**. Every check
here answers "if this silently stopped being read, what would I observe?" with an
observation rather than an assumption.

:class:`NegativeControls` runs each check against a deliberately broken tree, so a
check that has quietly stopped detecting anything fails here instead of passing
forever against a repository that happens to be correct.

Layout facts and citations: ``.claude/skills/claude-code-layout/references/``.
"""

import json
import re
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
DOT_CLAUDE = REPO_ROOT / ".claude"

# Directories Claude Code discovers *by location*. Anywhere else they are inert.
# https://code.claude.com/docs/en/claude-directory
DISCOVERED_DIRS = ("skills", "agents", "commands", "output-styles", "rules", "workflows")

# The only places a discovered directory may sit: `.claude/` at the repo root, or
# a nested `.claude/` in a subdirectory (monorepo packages). `templates/skills/`
# is this repo's distribution copy -- adopters copy it into their own
# `.claude/skills/`, so it is inert here on purpose.
ALLOWED_DISCOVERED_PARENTS = (".claude",)
# `.github/` is exempt because `.github/workflows/` is GitHub Actions -- same word,
# unrelated mechanism. The rest are trees where these names would be prose or data,
# not configuration anyone expects Claude Code to load.
EXEMPT_TREES = ("templates", ".git", ".github", "__pycache__", "history", "plans",
                "docs")

# Files directly under `.claude/` that Claude Code does not read. Allowed, but a
# deliberate choice: `workflow_config.json` is this repo's own config, loaded by
# `.claude/hooks/workflow_hook.py` through an explicit path. Adding to this list should
# be a visible decision in a diff.
NON_STANDARD_ALLOWED = frozenset({"workflow_config.json"})

STANDARD_CLAUDE_FILES = frozenset({
    "settings.json", "settings.local.json", "CLAUDE.md", "CLAUDE.local.md",
    "plugins.json", ".mcp.json",
})

# Directories that may sit directly under `.claude/`. The first six are
# discovered by location (DISCOVERED_DIRS); `agent-memory` is written by Claude
# Code itself; `hooks` is *not* discovered -- it holds scripts that only run
# because `settings.json` names them, and it is listed here so that the
# directory being present is a declared choice rather than an assumption.
# `workflow-core` is where an adopting project vendors this repository.
STANDARD_CLAUDE_DIRS = frozenset({
    "skills", "agents", "commands", "output-styles", "rules", "workflows",
    "agent-memory", "hooks", "plugins", "workflow-core",
})

# Every hook event Claude Code supports, as of v2.1.223. Listed so a typo in a
# settings file -- an event name that will simply never fire -- fails loudly.
# https://code.claude.com/docs/en/hooks
HOOK_EVENTS = frozenset({
    "SessionStart", "Setup", "UserPromptSubmit", "UserPromptExpansion",
    "PreToolUse", "PermissionRequest", "PermissionDenied", "PostToolUse",
    "PostToolUseFailure", "PostToolBatch", "Notification", "MessageDisplay",
    "SubagentStart", "SubagentStop", "TaskCreated", "TaskCompleted", "Stop",
    "StopFailure", "TeammateIdle", "InstructionsLoaded", "ConfigChange",
    "CwdChanged", "DirectoryAdded", "FileChanged", "WorktreeCreate",
    "WorktreeRemove", "PreCompact", "PostCompact", "Elicitation",
    "ElicitationResult", "SessionEnd",
})

# Settings files that must stay wired, and whether their script paths resolve in
# *this* tree. The template is here because it is what ships; omitting it is how
# the guard went missing for adopters. Its paths resolve only in an adopting
# project, so only its event names are checkable here.
SETTINGS_FILES = (
    (DOT_CLAUDE / "settings.json", True),
    (REPO_ROOT / "templates" / "settings.json.hooks", False),
)

AGENT_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frontmatter(text):
    """Flat ``key: value`` frontmatter reader -- stdlib only, no PyYAML."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("no frontmatter")
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1)
                   if line.strip() == "---")
    except StopIteration:
        raise ValueError("unterminated frontmatter") from None
    fields = {}
    for line in lines[1:end]:
        if not line.strip() or line.startswith((" ", "\t", "#", "-")):
            continue
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def misplaced_discovered_dirs(root):
    """Discovered directories sitting where Claude Code will never scan them."""
    found = []
    for path in root.rglob("*"):
        if not path.is_dir() or path.name not in DISCOVERED_DIRS:
            continue
        rel = path.relative_to(root)
        if set(rel.parts) & set(EXEMPT_TREES):
            continue
        if rel.parent.name in ALLOWED_DISCOVERED_PARENTS:
            continue
        found.append(rel.as_posix())
    return sorted(found)


def hook_problems(settings_path, root, check_paths=True):
    """Registered hooks whose event is unknown or whose script does not exist.

    ``check_paths`` is off for the adopter template: its commands resolve inside
    an adopting project, where this repository sits at
    ``.claude/workflow-core/``. That path does not exist *here*, because here is
    workflow-core itself. The template's command string is asserted separately by
    ``test_governance_library.SettingsWiring``, which knows the expected prefix.
    """
    problems = []
    if not settings_path.is_file():
        return [f"{settings_path.name}: missing"]
    hooks = (load_json(settings_path).get("hooks") or {})
    for event, entries in hooks.items():
        if event not in HOOK_EVENTS:
            problems.append(f"{settings_path.name}: '{event}' is not a hook event")
        if not check_paths:
            continue
        for entry in entries or []:
            for hook in (entry.get("hooks") or []):
                command = hook.get("command") or ""
                for token in re.findall(r'"?\$\{?CLAUDE_PROJECT_DIR\}?/([^"\s]+)"?',
                                        command):
                    if not (root / token).exists():
                        problems.append(
                            f"{settings_path.name}: {event} names a script that "
                            f"does not exist: {token}")
    return problems


def agent_problems(agents_dir):
    """Subagent files that will not load, or that collide by ``name``."""
    problems, seen = [], {}
    if not agents_dir.is_dir():
        return problems
    for path in sorted(agents_dir.rglob("*.md")):
        rel = path.name
        try:
            fields = parse_frontmatter(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            problems.append(f"{rel}: {exc}")
            continue
        name = fields.get("name")
        if not name:
            problems.append(f"{rel}: no `name` -- identity comes from the field, "
                            "not the filename")
        else:
            if ":" in name:
                problems.append(f"{rel}: name {name!r} contains ':', reserved for "
                                "plugin-scoped identifiers")
            elif not AGENT_NAME.match(name):
                problems.append(f"{rel}: name {name!r} is not lowercase kebab-case")
            if name in seen:
                problems.append(
                    f"{rel}: name {name!r} already used by {seen[name]} -- "
                    "duplicates resolve by filesystem read order, so which one "
                    "loads is undefined")
            seen[name] = rel
        if not fields.get("description"):
            problems.append(f"{rel}: no `description` -- Claude cannot decide to "
                            "delegate to it")
    return problems


# --------------------------------------------------------------------------- #
# The real tree
# --------------------------------------------------------------------------- #
class DiscoveredDirectories(unittest.TestCase):
    """A discovered directory outside `.claude/` is read by nothing."""

    def test_no_discovered_directory_sits_where_nothing_scans(self):
        self.assertEqual(
            [], misplaced_discovered_dirs(REPO_ROOT),
            "these are discovered by directory name, so outside `.claude/` they "
            "load nothing and report nothing -- the defect that hid this "
            "repository's skills for months")

    def test_the_skills_directory_is_present_and_populated(self):
        skills = DOT_CLAUDE / "skills"
        self.assertTrue(skills.is_dir(), ".claude/skills/ missing")
        self.assertTrue([p for p in skills.iterdir() if p.is_dir()],
                        ".claude/skills/ has no skills in it")


class HookRegistration(unittest.TestCase):
    """Hooks are wired by registration, so the registration is what to check."""

    def test_every_registered_hook_names_a_real_event_and_script(self):
        for settings, check_paths in SETTINGS_FILES:
            with self.subTest(settings=settings.name):
                self.assertEqual(
                    [], hook_problems(settings, REPO_ROOT, check_paths))

    def test_both_settings_files_register_the_same_events(self):
        """The template is what ships; drift from it is invisible to adopters."""
        events = {}
        for settings, _ in SETTINGS_FILES:
            events[settings.name] = set((load_json(settings).get("hooks") or {}))
        names = list(events)
        self.assertEqual(
            events[names[0]], events[names[1]],
            f"{names[0]} and {names[1]} register different hook events. The "
            "template is what adopters merge, so anything missing there is "
            "missing in every adopting project")


class SubagentFiles(unittest.TestCase):
    """Identity is the `name` field, and collisions resolve undefined."""

    def test_agent_files_are_loadable_and_uniquely_named(self):
        self.assertEqual([], agent_problems(DOT_CLAUDE / "agents"))


class NonStandardFiles(unittest.TestCase):
    """Unknown files under `.claude/` are ignored -- fine, but deliberately."""

    def test_unknown_files_are_on_the_allowlist(self):
        if not DOT_CLAUDE.is_dir():
            self.skipTest(".claude/ missing")
        unknown = sorted(
            p.name for p in DOT_CLAUDE.iterdir()
            if p.is_file() and p.name not in STANDARD_CLAUDE_FILES
            and p.name not in NON_STANDARD_ALLOWED)
        self.assertEqual(
            [], unknown,
            "Claude Code ignores these. That may be intended -- add them to "
            "NON_STANDARD_ALLOWED with a reason -- but an unlisted file is more "
            "often one someone expected to be read")

    def test_unknown_directories_are_on_the_allowlist(self):
        """The file check above missed `.claude/hooks/` entirely.

        ``iterdir`` was filtered on ``is_file()``, so any directory placed under
        ``.claude/`` was unexamined. A directory is the more consequential
        mistake of the two: a stray *file* is inert, but a directory named
        ``skill/`` or ``agent/`` looks discovered and is not.
        """
        if not DOT_CLAUDE.is_dir():
            self.skipTest(".claude/ missing")
        unknown = sorted(
            p.name for p in DOT_CLAUDE.iterdir()
            if p.is_dir() and p.name not in STANDARD_CLAUDE_DIRS)
        self.assertEqual(
            [], unknown,
            "Directories under `.claude/` that Claude Code does not read. Add to "
            "STANDARD_CLAUDE_DIRS with a reason if deliberate -- a near-miss name "
            "like `skill/` or `rule/` is discovered by nothing and reports nothing")


class RulePathsFrontmatter(unittest.TestCase):
    """`paths:` is a glob list, and a malformed one matches nothing -- silently.

    Criteria are from https://code.claude.com/docs/en/memory#path-specific-rules,
    verified 2026-08-06 against v2.1.223. The bracket rule is the valuable one:
    "A pattern with a `[` that can't be read as a bracket expression ... matches
    nothing, and the rule's other patterns keep working." So a typo costs you the
    rule with no error anywhere.
    """

    RULES = DOT_CLAUDE / "rules"

    def rule_files(self):
        if not self.RULES.is_dir():
            return []
        return sorted(self.RULES.rglob("*.md"))

    @staticmethod
    def paths_block(text):
        """Return the `paths:` list, or None when the rule is unconditional."""
        lines = text.splitlines()
        if not lines or lines[0].strip() != "---":
            return None
        try:
            end = next(i for i, l in enumerate(lines[1:], start=1) if l.strip() == "---")
        except StopIteration:
            return None
        block, collecting = [], False
        for line in lines[1:end]:
            if line.strip().startswith("paths:"):
                collecting = True
                continue
            if collecting:
                stripped = line.strip()
                if stripped.startswith("- "):
                    block.append(stripped[2:].strip().strip('"').strip("'"))
                elif stripped and not line.startswith((" ", "\t")):
                    break
        return block if collecting else None

    def test_paths_lists_are_well_formed(self):
        for path in self.rule_files():
            patterns = self.paths_block(path.read_text(encoding="utf-8"))
            if patterns is None:
                continue  # unconditional rule -- loads at session start
            with self.subTest(rule=path.name):
                self.assertTrue(
                    patterns,
                    "`paths:` present but empty -- omit the field instead; a rule "
                    "without it loads unconditionally, one with an empty list is "
                    "ambiguous")
                for pattern in patterns:
                    bare = _unescaped_brackets(pattern)
                    self.assertEqual(
                        bare.count("["), bare.count("]"),
                        f"{pattern!r}: unbalanced '[' is read as a bracket "
                        "expression and matches NOTHING -- escape it as '\\['")
                    self.assertLessEqual(
                        _brace_expansion_size(pattern), 1000,
                        f"{pattern!r}: exceeds the documented 1,000-pattern brace "
                        "budget; Claude Code then uses it unexpanded and its "
                        "literal braces match no files")

    def test_unconditional_rules_carry_no_paths(self):
        """Anything that must survive `/compact` must not be path-scoped.

        Path-scoped rules "are not re-injected automatically" after compaction --
        they reload only when a matching file is next read. A rule that must hold
        unconditionally therefore cannot be gated.
        """
        for name in ("repo-conventions.md", "governance-library.md"):
            path = self.RULES / name
            if not path.is_file():
                continue
            with self.subTest(rule=name):
                self.assertIsNone(
                    self.paths_block(path.read_text(encoding="utf-8")),
                    f"{name} must load every session; a `paths:` gate would drop "
                    "it after /compact until a matching file happens to be read")


class TemplateMirrors(unittest.TestCase):
    """`.claude/rules/` and `.claude/agents/` ship to adopters too.

    Same reasoning as ``templates/skills/`` and ``templates/ai-library/``: adopters
    vendor this repo at ``.claude/workflow-core/``, where these directories sit at
    a nested path Claude Code does not read as theirs. They copy from
    ``templates/``. A directory added here and not there is a directory adopters
    never get.
    """

    PAIRS = (("rules", DOT_CLAUDE / "rules", REPO_ROOT / "templates" / "rules"),
             ("agents", DOT_CLAUDE / "agents", REPO_ROOT / "templates" / "agents"))

    def test_mirrors_exist_and_match(self):
        for label, source, template in self.PAIRS:
            with self.subTest(tree=label):
                if not source.is_dir():
                    self.skipTest(f".claude/{label}/ absent")
                self.assertTrue(template.is_dir(),
                                f"templates/{label}/ missing -- adopters get nothing")
                src = {p.relative_to(source).as_posix() for p in source.rglob("*.md")}
                tpl = {p.relative_to(template).as_posix() for p in template.rglob("*.md")}
                self.assertEqual(src, tpl, f"templates/{label}/ has drifted")
                for rel in sorted(src):
                    self.assertEqual(
                        (source / rel).read_bytes(), (template / rel).read_bytes(),
                        f"{label}/{rel}: source and template have diverged")


def _unescaped_brackets(pattern):
    r"""Drop backslash-escaped brackets before counting.

    ``photos \[2024/**`` is the *documented* way to match a literal '['. A first
    draft counted raw characters and rejected it -- flagging the correct form as
    the error. Found by running the check against the docs' own example rather
    than reasoning about it.
    """
    return re.sub(r"\\.", "", pattern)


def _brace_expansion_size(pattern):
    """Product of brace-group sizes -- the documented budget is per rule, per pattern."""
    total = 1
    for group in re.findall(r"\{([^{}]*)\}", pattern):
        total *= max(1, group.count(",") + 1)
    return total


class LocalSettingsAreIgnored(unittest.TestCase):
    """A machine-global ignore rule protects one checkout, not the repository."""

    def test_settings_local_is_ignored_by_this_repos_gitignore(self):
        gitignore = REPO_ROOT / ".gitignore"
        self.assertTrue(gitignore.is_file(), ".gitignore missing")
        self.assertIn(
            ".claude/settings.local.json",
            gitignore.read_text(encoding="utf-8"),
            "settings.local.json holds personal permission grants. Without a rule "
            "in the repo's own .gitignore it is only ignored on machines that "
            "happen to have a global rule, and `git add -A` commits it anywhere else")

    def test_git_agrees_and_the_rule_is_the_repos_own(self):
        """Belt and braces: ask git, with the global ignore file disabled."""
        result = subprocess.run(
            ["git", "-c", "core.excludesFile=/dev/null", "check-ignore", "-v",
             ".claude/settings.local.json"],
            cwd=REPO_ROOT, capture_output=True, text=True)
        if result.returncode == 128:
            self.skipTest("git unavailable")
        self.assertEqual(
            0, result.returncode,
            "git does not ignore .claude/settings.local.json using the repo's "
            "own rules")
        self.assertTrue(
            result.stdout.startswith(".gitignore:"),
            f"the matching rule is not the repo's .gitignore: {result.stdout.strip()}")


# --------------------------------------------------------------------------- #
# Negative controls
# --------------------------------------------------------------------------- #
class NegativeControls(unittest.TestCase):
    """Each check, run against something it must reject.

    The real tree is correct, so every check above passes whether or not it still
    works. These prove the checks still bite, without committing a broken tree.
    """

    def tmp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Path(tmp.name)

    def test_a_repo_root_skills_directory_is_caught(self):
        root = self.tmp()
        (root / "skills" / "my-skill").mkdir(parents=True)
        self.assertIn("skills", misplaced_discovered_dirs(root))

    def test_a_near_miss_directory_under_dot_claude_is_caught(self):
        """`.claude/skill/` (singular) is discovered by nothing and reports nothing."""
        for name in ("skill", "rule", "agent", "hook"):
            with self.subTest(directory=name):
                self.assertNotIn(
                    name, STANDARD_CLAUDE_DIRS,
                    f"'{name}' is a near-miss of a real directory and must not be "
                    "allowlisted -- allowlisting it hides exactly the typo the "
                    "check exists to catch")

    def test_the_real_hooks_directory_is_allowlisted(self):
        """`.claude/hooks/` is legitimate but *not* discovered -- a declared choice."""
        self.assertIn("hooks", STANDARD_CLAUDE_DIRS)
        self.assertNotIn(
            "hooks", DISCOVERED_DIRS,
            "hooks/ is registered in settings.json, never discovered by location; "
            "listing it as discovered would teach the opposite of the failure mode")

    def test_every_discovered_kind_is_caught(self):
        root = self.tmp()
        for name in DISCOVERED_DIRS:
            (root / "misc" / name).mkdir(parents=True)
        self.assertEqual(
            sorted(f"misc/{n}" for n in DISCOVERED_DIRS),
            misplaced_discovered_dirs(root))

    def test_a_correctly_placed_directory_is_not_caught(self):
        root = self.tmp()
        (root / ".claude" / "skills").mkdir(parents=True)
        (root / "packages" / "web" / ".claude" / "agents").mkdir(parents=True)
        self.assertEqual([], misplaced_discovered_dirs(root))

    def test_an_unknown_hook_event_is_caught(self):
        root = self.tmp()
        settings = root / "settings.json"
        settings.write_text(json.dumps(
            {"hooks": {"PreToolUpe": [{"hooks": [{"type": "command",
                                                  "command": "echo hi"}]}]}}),
            encoding="utf-8")
        self.assertTrue(any("is not a hook event" in p
                            for p in hook_problems(settings, root)))

    def test_a_hook_naming_a_missing_script_is_caught(self):
        root = self.tmp()
        settings = root / "settings.json"
        settings.write_text(json.dumps(
            {"hooks": {"PreToolUse": [{"hooks": [
                {"type": "command",
                 "command": 'python "$CLAUDE_PROJECT_DIR/hooks/absent.py"'}]}]}}),
            encoding="utf-8")
        self.assertTrue(any("does not exist" in p
                            for p in hook_problems(settings, root)))

    def test_a_hook_naming_a_real_script_is_accepted(self):
        root = self.tmp()
        (root / "hooks").mkdir()
        (root / "hooks" / "present.py").write_text("x", encoding="utf-8")
        settings = root / "settings.json"
        settings.write_text(json.dumps(
            {"hooks": {"PreToolUse": [{"hooks": [
                {"type": "command",
                 "command": 'python "$CLAUDE_PROJECT_DIR/hooks/present.py"'}]}]}}),
            encoding="utf-8")
        self.assertEqual([], hook_problems(settings, root))

    def _agent(self, root, filename, frontmatter):
        agents = root / "agents"
        agents.mkdir(exist_ok=True)
        (agents / filename).write_text(frontmatter, encoding="utf-8")
        return agents

    def test_an_agent_without_a_name_is_caught(self):
        root = self.tmp()
        agents = self._agent(root, "a.md", "---\ndescription: Does things.\n---\n")
        self.assertTrue(any("no `name`" in p for p in agent_problems(agents)))

    def test_an_agent_without_a_description_is_caught(self):
        root = self.tmp()
        agents = self._agent(root, "a.md", "---\nname: reviewer\n---\n")
        self.assertTrue(any("no `description`" in p for p in agent_problems(agents)))

    def test_a_colon_in_an_agent_name_is_caught(self):
        root = self.tmp()
        agents = self._agent(
            root, "a.md", "---\nname: mine:reviewer\ndescription: X.\n---\n")
        self.assertTrue(any("contains ':'" in p for p in agent_problems(agents)))

    def test_duplicate_agent_names_are_caught(self):
        root = self.tmp()
        body = "---\nname: reviewer\ndescription: X.\n---\n"
        self._agent(root, "one.md", body)
        agents = self._agent(root, "two.md", body)
        self.assertTrue(any("already used by" in p for p in agent_problems(agents)))

    def test_a_well_formed_agent_is_accepted(self):
        root = self.tmp()
        agents = self._agent(
            root, "code-reviewer.md",
            "---\nname: code-reviewer\ndescription: Reviews code.\n---\nBody.\n")
        self.assertEqual([], agent_problems(agents))


if __name__ == "__main__":
    unittest.main()
