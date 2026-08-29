#!/usr/bin/env python3
"""Structure tests for the skills under ``.claude/skills/``.

Stdlib ``unittest`` only -- run with::

    python -m unittest discover -s tests
    # or
    python -m unittest tests.test_skills

Skills are the one artifact in this repository whose *location* is load-bearing
in a way nothing here can see. Claude Code discovers skills at
``~/.claude/skills/``, the project ``.claude/skills/`` (plus nested ones below
the working directory) and plugin directories -- and nowhere else. This
repository kept its skills in a repo-root ``skills/`` directory until
2026-08-06, where every frontmatter field in them, including the
``disallowed-tools`` that was supposed to remove ``AskUserQuestion``, was inert.
Nothing failed, because nothing was checking.

So this module checks the things that otherwise fail silently:

* the skills live where Claude Code looks, and the old path is gone (:class:`StalePathScan`);
* frontmatter keys are real ones, since an unrecognised key is ignored without
  a warning -- ``user-invokable`` for ``user-invocable`` does nothing at all;
* bodies stay inside the documented 500-line cap, and are flagged before they
  pass the ~5,000-token compaction re-attach cut-off, past which the tail of a
  skill silently disappears;
* every reference a ``SKILL.md`` links to exists;
* ``templates/skills/`` -- what adopters copy -- has not fallen behind.

:class:`NegativeControls` runs the same checks against deliberately broken
synthetic skills, so a check that has quietly stopped detecting anything fails
here rather than passing forever.

Facts and citations behind the constants:
``.claude/skills/skill-authoring/references/verified-facts.md``.
"""

import re
import unittest
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS = REPO_ROOT / ".claude" / "skills"
TEMPLATE_SKILLS = REPO_ROOT / "templates" / "skills"

# Documented recommendation: "Keep SKILL.md under 500 lines."
# https://code.claude.com/docs/en/skills
MAX_BODY_LINES = 500

# After auto-compaction Claude Code re-attaches only the first 5,000 tokens of
# each invoked skill. Past this the tail is dropped with no diagnostic, which is
# why it is worth flagging -- but the budget is a documented implementation
# detail that can move, so exceeding it warns rather than fails. Edit here.
SKILL_TOKEN_BUDGET = 5000

# Characters per token, for the proxy. Line counts measure wrapping, not
# content: this repository's skill markdown runs ~59 chars/line, so a line-based
# proxy misjudges a dense file by more than a factor of two.
CHARS_PER_TOKEN = 4

# `description` + `when_to_use` are truncated at 1,536 characters in the skill
# listing. The open standard caps `description` itself at 1,024; the tighter of
# the two is the useful limit to hold authors to.
MAX_DESCRIPTION_CHARS = 1024

# Every field Claude Code documents. Anything outside this set is ignored
# silently at runtime, so an unknown key here is a typo, not an extension.
KNOWN_FRONTMATTER_KEYS = frozenset({
    "name", "description", "when_to_use", "argument-hint", "arguments",
    "disable-model-invocation", "user-invocable", "allowed-tools",
    "disallowed-tools", "model", "effort", "context", "agent", "background",
    "hooks", "paths", "shell",
})

# https://agentskills.io/specification -- lowercase alphanumeric segments joined
# by single hyphens. Subsumes "no leading/trailing hyphen" and "no consecutive
# hyphens" in one expression rather than three separate assertions.
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME_CHARS = 64

# Files worth scanning for the stale path, and trees to leave alone.
SCANNED_SUFFIXES = frozenset({".md", ".json", ".py", ".yaml", ".yml", ".fragment", ".txt"})
# `history/` and `plans/archive/` are append-only audit trails (Tier 0): the old
# paths recorded there are the record, not an error to correct.
UNSCANNED_DIRS = frozenset({".git", "__pycache__", "history", "archive", ".pytest_cache"})
# Same reasoning for the changelogs -- they describe releases as they were, and
# editing a shipped entry to name today's path would misreport what shipped.
# This module is exempt because it is the scanner: it has to quote the pattern
# it looks for.
UNSCANNED_FILES = frozenset({
    "CHANGELOG.md", "GUIDE_CHANGELOG.md", "tests/test_skills.py",
})

# Markdown links that point at something on disk, as opposed to a URL or anchor.
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def parse_frontmatter(text):
    """Return ``(fields, body)`` for a ``SKILL.md``.

    Deliberately a flat ``key: value`` reader rather than a YAML parse: skill
    frontmatter is flat, and ``.claude/hooks/workflow_hook.py`` is stdlib-only so that
    adopters can vendor this repository without acquiring a dependency tree.
    A block value (``key:`` followed by an indented block) records the key with
    an empty value -- enough for the key-name checks, which is all this needs.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("no frontmatter: file does not open with '---'")
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1)
                   if line.strip() == "---")
    except StopIteration:
        raise ValueError("unterminated frontmatter: no closing '---'") from None

    fields = {}
    for line in lines[1:end]:
        if not line.strip() or line.startswith((" ", "\t", "#", "-")):
            continue  # continuation of a block value, comment, or list item
        key, sep, value = line.partition(":")
        if not sep:
            raise ValueError(f"frontmatter line is not 'key: value': {line!r}")
        fields[key.strip()] = value.strip()
    return fields, "\n".join(lines[end + 1:])


def skill_dirs(root):
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


def violations(skill_dir):
    """Every hard-failure violation for one skill directory, as strings.

    Returns a list so a broken skill reports all of its problems at once
    instead of one per fix-and-rerun cycle. The token-budget check is *not*
    here; it warns, and lives in :meth:`SkillStructure.test_token_budget`.
    """
    found = []
    skill_md = skill_dir / "SKILL.md"

    # Compare against the real directory entries rather than trusting
    # ``is_file()``: Windows and macOS filesystems are case-insensitive, so a
    # ``skill.md`` that Claude Code would never load answers ``is_file()`` for
    # ``SKILL.md`` and reads back cleanly. The name has to be checked as data.
    entries = {p.name for p in skill_dir.iterdir() if p.is_file()}
    if "SKILL.md" not in entries:
        misnamed = sorted(n for n in entries if n.lower() == "skill.md")
        if misnamed:
            return [f"entrypoint is {misnamed[0]!r}, must be exactly 'SKILL.md'"]
        return ["no SKILL.md"]

    text = skill_md.read_text(encoding="utf-8")
    try:
        fields, body = parse_frontmatter(text)
    except ValueError as exc:
        return found + [str(exc)]

    unknown = sorted(set(fields) - KNOWN_FRONTMATTER_KEYS)
    if unknown:
        found.append(
            f"unknown frontmatter key(s) {unknown} -- ignored silently at runtime; "
            f"known keys: {sorted(KNOWN_FRONTMATTER_KEYS)}")

    name = fields.get("name")
    if name is not None:
        if name != skill_dir.name:
            found.append(
                f"name {name!r} != directory {skill_dir.name!r} -- the directory "
                f"supplies the command, so these disagreeing is a trap")
        if len(name) > MAX_NAME_CHARS:
            found.append(f"name is {len(name)} chars, max {MAX_NAME_CHARS}")
        if not NAME_PATTERN.match(name):
            found.append(f"name {name!r} is not lowercase kebab-case")

    description = fields.get("description")
    if not description:
        found.append("no description -- it is all Claude sees when deciding to load the skill")
    elif len(description) > MAX_DESCRIPTION_CHARS:
        found.append(f"description is {len(description)} chars, max {MAX_DESCRIPTION_CHARS}")

    body_lines = len(body.splitlines())
    if body_lines > MAX_BODY_LINES:
        found.append(f"body is {body_lines} lines, max {MAX_BODY_LINES}")

    found.extend(broken_links(skill_md))
    return found


def broken_links(md_path):
    """Relative markdown links from ``md_path`` that do not resolve on disk."""
    text = md_path.read_text(encoding="utf-8")
    broken = []
    for target in MD_LINK.findall(text):
        target = target.split("#", 1)[0].strip()
        if not target or "://" in target or target.startswith(("#", "mailto:")):
            continue
        if not (md_path.parent / target).exists():
            broken.append(f"broken link: {target}")
    return broken


def estimated_tokens(path):
    return len(path.read_text(encoding="utf-8")) // CHARS_PER_TOKEN


def stale_path_pattern(names):
    """A ``skills/<name>`` reference that is neither ``.claude/`` nor ``templates/``.

    Anchored on the real skill names rather than on the bare word ``skills``, so
    prose *about* the defect ("a repo-root ``skills/`` folder is not discovered")
    and unrelated paths like a plugin's own ``<plugin>/skills/<name>`` don't trip
    it. Only a reference that would actually send someone to the dead location
    counts.
    """
    alternatives = "|".join(re.escape(n) for n in sorted(names))
    return re.compile(
        r"(?<!\.claude/)(?<!\.claude\\)(?<!templates/)(?<!templates\\)"
        r"\bskills[/\\](?:" + alternatives + r")\b")


def scannable_files(root):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
            continue
        rel = path.relative_to(root)
        if UNSCANNED_DIRS & set(rel.parts):
            continue
        if rel.as_posix() in UNSCANNED_FILES:
            continue
        yield path


def relative_files(root):
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


# --------------------------------------------------------------------------- #
# The real skills
# --------------------------------------------------------------------------- #
class SkillStructure(unittest.TestCase):
    """Every skill in ``.claude/skills/`` is one Claude Code can actually load."""

    def test_skills_directory_is_where_claude_code_looks(self):
        self.assertTrue(
            SKILLS.is_dir(),
            ".claude/skills/ missing -- skills anywhere else are not discovered")
        self.assertTrue(skill_dirs(SKILLS), ".claude/skills/ has no skills in it")

    def test_no_skills_at_the_undiscovered_repo_root_path(self):
        self.assertFalse(
            (REPO_ROOT / "skills").exists(),
            "repo-root skills/ is back -- Claude Code does not discover it; "
            "the correct location is .claude/skills/")

    def test_each_skill_is_well_formed(self):
        for skill in skill_dirs(SKILLS):
            with self.subTest(skill=skill.name):
                self.assertEqual([], violations(skill))

    def test_directory_names_are_kebab_case(self):
        for skill in skill_dirs(SKILLS):
            with self.subTest(skill=skill.name):
                self.assertRegex(skill.name, NAME_PATTERN,
                                 "the directory name becomes the /command")
                self.assertLessEqual(len(skill.name), MAX_NAME_CHARS)

    def test_reference_files_resolve(self):
        """Links inside references/ too -- a dead link there fails just as quietly."""
        for skill in skill_dirs(SKILLS):
            for md in sorted(skill.rglob("*.md")):
                with self.subTest(file=md.relative_to(SKILLS).as_posix()):
                    self.assertEqual([], broken_links(md))

    def test_token_budget(self):
        """Warn before a body passes the compaction re-attach cut-off.

        Not a failure: the 5,000-token figure is an implementation detail that
        can move, and a hard gate on a moving number invites the wrong fix
        (deleting content that matters) over the right one (splitting).
        """
        for skill in skill_dirs(SKILLS):
            skill_md = skill / "SKILL.md"
            if not skill_md.is_file():
                continue
            tokens = estimated_tokens(skill_md)
            if tokens > SKILL_TOKEN_BUDGET:
                warnings.warn(
                    f"{skill.name}/SKILL.md is ~{tokens} tokens, over the "
                    f"{SKILL_TOKEN_BUDGET}-token compaction re-attach budget: "
                    f"the tail will be dropped silently after a compaction. "
                    f"Move detail into references/.",
                    stacklevel=2)


# --------------------------------------------------------------------------- #
# Negative controls
# --------------------------------------------------------------------------- #
class NegativeControls(unittest.TestCase):
    """Each check, run against something it should reject.

    A check that has stopped detecting its defect passes the suite above
    forever, because the real skills are correct. These prove the checks still
    bite. Built as synthetic skills in a temp directory rather than fixtures on
    disk, so nothing broken is ever committed to ``.claude/skills/``.
    """

    def build(self, frontmatter, body="# Title\n", extra_files=()):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        skill = Path(tmp.name) / "sample-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text(frontmatter + body, encoding="utf-8")
        for rel in extra_files:
            (skill / rel).write_text("x", encoding="utf-8")
        return skill

    def assertRejects(self, skill, fragment):
        found = violations(skill)
        self.assertTrue(
            any(fragment in v for v in found),
            f"expected a violation containing {fragment!r}, got {found}")

    GOOD = "---\nname: sample-skill\ndescription: A sample.\n---\n"

    def test_a_correct_skill_passes(self):
        """Guards the other cases: rejection must come from the defect, not the harness."""
        self.assertEqual([], violations(self.build(self.GOOD)))

    def test_misspelled_user_invokable_is_rejected(self):
        # The exact typo the supplied guide's validator list contained. At
        # runtime it is accepted and ignored, which is the whole problem.
        self.assertRejects(
            self.build("---\nname: sample-skill\ndescription: A sample.\n"
                       "user-invokable: false\n---\n"),
            "unknown frontmatter key(s) ['user-invokable']")

    def test_missing_description_is_rejected(self):
        self.assertRejects(self.build("---\nname: sample-skill\n---\n"), "no description")

    def test_name_not_matching_directory_is_rejected(self):
        self.assertRejects(
            self.build("---\nname: other-name\ndescription: A sample.\n---\n"),
            "!= directory")

    def test_consecutive_hyphens_in_name_are_rejected(self):
        skill = self.build("---\nname: sample--skill\ndescription: A sample.\n---\n")
        (skill.parent / "sample--skill").mkdir()
        (skill / "SKILL.md").rename(skill.parent / "sample--skill" / "SKILL.md")
        self.assertRejects(skill.parent / "sample--skill", "not lowercase kebab-case")

    def test_over_length_body_is_rejected(self):
        body = "\n".join(f"line {i}" for i in range(MAX_BODY_LINES + 10))
        self.assertRejects(self.build(self.GOOD, body=body),
                           f"max {MAX_BODY_LINES}")

    def test_over_length_description_is_rejected(self):
        long = "x" * (MAX_DESCRIPTION_CHARS + 1)
        self.assertRejects(
            self.build(f"---\nname: sample-skill\ndescription: {long}\n---\n"),
            f"max {MAX_DESCRIPTION_CHARS}")

    def test_dead_reference_link_is_rejected(self):
        self.assertRejects(
            self.build(self.GOOD, body="See [notes](references/absent.md)\n"),
            "broken link: references/absent.md")

    def test_live_reference_link_is_accepted(self):
        skill = self.build(self.GOOD, body="See [notes](notes.md)\n")
        (skill / "notes.md").write_text("x", encoding="utf-8")
        self.assertEqual([], violations(skill))

    def test_urls_and_anchors_are_not_treated_as_files(self):
        skill = self.build(
            self.GOOD,
            body="[docs](https://code.claude.com/docs/en/skills) and [top](#title)\n")
        self.assertEqual([], violations(skill))

    def test_missing_frontmatter_is_rejected(self):
        self.assertRejects(self.build("", body="# Just a heading\n"), "no frontmatter")

    def test_unterminated_frontmatter_is_rejected(self):
        self.assertRejects(
            self.build("---\nname: sample-skill\n", body="body\n"),
            "unterminated frontmatter")

    def test_missing_skill_md_is_rejected(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        empty = Path(tmp.name) / "empty-skill"
        empty.mkdir()
        self.assertRejects(empty, "no SKILL.md")

    def test_lowercase_skill_md_is_rejected(self):
        """The check that a case-insensitive filesystem would otherwise hide."""
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        skill = Path(tmp.name) / "sample-skill"
        skill.mkdir()
        (skill / "skill.md").write_text(self.GOOD, encoding="utf-8")
        self.assertRejects(skill, "must be exactly 'SKILL.md'")

    def test_token_proxy_measures_characters_not_lines(self):
        """The basis for the proxy, asserted rather than assumed.

        A few very long lines are over budget; many short ones are not. A
        line-count proxy gets both backwards.
        """
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        dense = Path(tmp.name) / "dense.md"
        dense.write_text("x" * (SKILL_TOKEN_BUDGET * CHARS_PER_TOKEN + 100), encoding="utf-8")
        sparse = Path(tmp.name) / "sparse.md"
        sparse.write_text("x\n" * 400, encoding="utf-8")

        self.assertGreater(estimated_tokens(dense), SKILL_TOKEN_BUDGET,
                           "3 lines of dense prose can exceed the budget")
        self.assertLess(estimated_tokens(sparse), SKILL_TOKEN_BUDGET,
                        "400 short lines need not exceed it")


# --------------------------------------------------------------------------- #
# The old path stays gone
# --------------------------------------------------------------------------- #
class StalePathScan(unittest.TestCase):
    """No document may send a reader back to the location that never worked.

    This is the drift check, in place of a single-source-of-truth paths file:
    the references live in prose written for different audiences, and a registry
    would be one more thing that can go stale. A test cannot.
    """

    def test_no_file_references_the_repo_root_skills_path(self):
        self.maxDiff = None
        pattern = stale_path_pattern(p.name for p in skill_dirs(SKILLS))
        offenders = []
        for path in scannable_files(REPO_ROOT):
            rel = path.relative_to(REPO_ROOT).as_posix()
            for number, line in enumerate(
                    path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if pattern.search(line):
                    offenders.append(f"{rel}:{number}: {line.strip()}")
        self.assertEqual(
            [], offenders,
            "these name a repo-root skills/ path, which Claude Code does not "
            "discover -- use .claude/skills/ (or templates/skills/ for the "
            "adopter copy):\n" + "\n".join(offenders))

    def test_the_scanner_would_catch_a_regression(self):
        pattern = stale_path_pattern(["adaptive-workflow"])
        self.assertRegex("see skills/adaptive-workflow/SKILL.md", pattern)
        self.assertRegex(r"see skills\adaptive-workflow\SKILL.md", pattern)
        self.assertNotRegex(".claude/skills/adaptive-workflow/SKILL.md", pattern)
        self.assertNotRegex("templates/skills/adaptive-workflow/SKILL.md", pattern)
        self.assertNotRegex("a repo-root `skills/` folder is not discovered", pattern)
        self.assertNotRegex("<plugin>/skills/<name>/SKILL.md", pattern)


# --------------------------------------------------------------------------- #
# Adopter template parity
# --------------------------------------------------------------------------- #
class SkillTemplateParity(unittest.TestCase):
    """``templates/skills/`` is what adopters copy; it must not fall behind.

    Adopters vendor this repository at ``.claude/workflow-core/``, where its own
    ``.claude/skills/`` would sit at a nested path that loads only incidentally.
    So the distribution copy lives in ``templates/`` and they copy it into their
    own ``.claude/skills/``. Same reasoning, and same enforcement, as
    ``.ai/`` -> ``templates/ai-library/``.
    """

    def test_file_trees_match(self):
        self.assertTrue(TEMPLATE_SKILLS.is_dir(), f"{TEMPLATE_SKILLS} missing")
        source, template = relative_files(SKILLS), relative_files(TEMPLATE_SKILLS)
        self.assertEqual(set(), source - template,
                         "in .claude/skills/ but missing from templates/skills/")
        self.assertEqual(set(), template - source,
                         "in templates/skills/ but missing from .claude/skills/")

    def test_files_are_identical(self):
        for rel in sorted(relative_files(SKILLS) & relative_files(TEMPLATE_SKILLS)):
            with self.subTest(file=rel):
                self.assertEqual(
                    (SKILLS / rel).read_bytes(), (TEMPLATE_SKILLS / rel).read_bytes(),
                    f"{rel}: .claude/skills/ and templates/skills/ have diverged")


class VerificationStamps(unittest.TestCase):
    """Files asserting Claude Code behaviour must say when they were last checked.

    Claude Code ships several times a week. A reference file claiming what a
    frontmatter field does, or which directories are discovered, is a claim about
    a moving target -- and this repository has already carried one that went stale
    within days of being written, against a runtime two versions newer, with
    nothing observing it. The stamp is what makes staleness visible; without it
    a wrong claim and a right one look identical.

    The check is deliberately narrow. It does not know whether the *content* is
    still true -- nothing here could. It only enforces that the claim is dated
    and version-bound, so ``--self-test`` can nag when the date ages past
    ``revalidation_interval_days``.
    """

    #: ``Verified 2026-08-06 against Claude Code v2.1.223`` -- surrounding prose is free.
    STAMP = re.compile(
        r"[Vv]erified\s+(?:on\s+)?\*{0,2}(\d{4}-\d{2}-\d{2})\*{0,2}\s+against\s+"
        r"(?:Claude Code\s+)?\*{0,2}v(\d+\.\d+\.\d+)\*{0,2}")

    #: A version reference is a claim about a specific release, so it dates itself
    #: or it misleads.
    VERSION_MENTION = re.compile(r"\bv\d+\.\d+\.\d+\b")

    #: Sustained discussion of the product, rather than one passing mention.
    #: A first draft counted keywords like "hook" and "frontmatter" instead, and
    #: flagged `conditional-triggers.md` -- a file about *this repository's*
    #: workflow triggers that names those things only in passing. A check that
    #: cries wolf gets suppressed, so the trigger is narrower now: talking about
    #: Claude Code repeatedly, or citing a version number.
    PRODUCT_MENTION_THRESHOLD = 3

    def stamped_files(self):
        for path in sorted(SKILLS.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            yield path.relative_to(REPO_ROOT).as_posix(), text

    def needs_stamp(self, text):
        return (text.lower().count("claude code") >= self.PRODUCT_MENTION_THRESHOLD
                or bool(self.VERSION_MENTION.search(text)))

    def test_files_asserting_behaviour_carry_a_stamp(self):
        missing = [rel for rel, text in self.stamped_files()
                   if self.needs_stamp(text) and not self.STAMP.search(text)]
        self.assertEqual(
            [], missing,
            "These discuss Claude Code's own behaviour, or cite a version, but carry "
            "no verification stamp. Add `Verified YYYY-MM-DD against Claude Code "
            "vX.Y.Z`, or move the claims into a reference file that has one")

    def test_stamps_are_well_formed_and_not_from_the_future(self):
        import datetime
        today = datetime.date.today()
        for rel, text in self.stamped_files():
            match = self.STAMP.search(text)
            if not match:
                continue
            with self.subTest(file=rel):
                stamped = datetime.date.fromisoformat(match.group(1))
                self.assertLessEqual(
                    stamped, today,
                    f"{rel}: stamped {stamped}, which is in the future")

    def test_all_stamps_agree_on_the_version(self):
        """One re-verification pass, one version -- a split means one was forgotten.

        This is the realistic drift: someone re-checks the file they are editing
        and leaves its neighbour behind, so the tree claims two different
        runtimes at once and neither reader can tell which is current.
        """
        versions = {}
        for rel, text in self.stamped_files():
            match = self.STAMP.search(text)
            if match:
                versions.setdefault(match.group(2), []).append(rel)
        self.assertLessEqual(
            len(versions), 1,
            f"Verification stamps disagree on the Claude Code version: {versions}. "
            "Re-verify the stragglers rather than editing the number")


# --------------------------------------------------------------------------- #
# Corpus guards
# --------------------------------------------------------------------------- #
class CorpusNotEmpty(unittest.TestCase):
    """Every check in this module loops over a directory. An empty one passes them all.

    A test that iterates a corpus and finds nothing does not fail -- it reports
    success, having verified nothing at all. That is the single most expensive
    failure mode in this repository's history, because the suite stays green
    while the thing it was guarding is gone.

    These assertions are the floor under every loop above. They are deliberately
    crude: they do not check content, only that there is content to check. If a
    directory is legitimately emptied one day, the fix is to delete the tests
    that read it in the same commit -- not to loosen this class.

    Added 2026-08-29, before the `.ai/` retirement, precisely because that
    migration empties directories other tests iterate.
    """

    def test_skills_are_present(self):
        self.assertTrue(skill_dirs(SKILLS),
                        f"{SKILLS} has no skill directories -- every per-skill "
                        "check in this module is passing vacuously")

    def test_template_skills_are_present(self):
        """Directories *and* content.

        `skill_dirs` counts folders, so deleting every SKILL.md while leaving the
        folders would pass a directory-only check -- the same vacuous shape this
        class exists to close, one level down. Caught by the gate auditor on
        2026-08-29 reviewing the first version of this test.
        """
        self.assertTrue(skill_dirs(TEMPLATE_SKILLS),
                        f"{TEMPLATE_SKILLS} is empty -- the parity tests compare "
                        "nothing to nothing and adopters get no skills")
        self.assertTrue(list(TEMPLATE_SKILLS.rglob("SKILL.md")),
                        f"{TEMPLATE_SKILLS} has skill folders but no SKILL.md in "
                        "any of them -- adopters get empty directories")

    def test_markdown_corpus_is_present(self):
        """`stamped_files` and the link checks read this; empty means no coverage."""
        self.assertTrue(list(SKILLS.rglob("*.md")),
                        f"no .md files under {SKILLS}")


if __name__ == "__main__":
    unittest.main()
