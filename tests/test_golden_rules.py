#!/usr/bin/env python3
"""Shape tests for the markdown rule library under ``golden-rules/``.

Stdlib ``unittest`` only -- run with::

    python -m unittest discover -s tests
    # or
    python -m unittest tests.test_golden_rules

Until 2026-08-30 **no test in this repository touched ``golden-rules/`` at all**.
The library that is scheduled to replace `.ai/` was entirely unenforced while
the thing it replaces carried a 959-line test file, which is the wrong way round
for a migration whose stated risk is "the same complexity relocated from
schema-enforced to prose-enforced, with the tests that caught drift deleted".

The format has no schema and no frontmatter by design, so what is checkable is
narrow and deliberately so. Three properties, each chosen because losing it
silently is the failure this library is supposed to be immune to:

* **``Status:`` is one of exactly two forms, with a real, non-future date.** The
  whole two-layer split rests on being able to tell a human-reviewed file from an
  agent-drafted one at a glance. A free-text stamp degrades to decoration.
* **Every ``##`` group carries exactly one ``Sources:`` line, and that line is
  version-pinned.** This is the criterion gate 2 of
  ``plans/golden-rules-migration.md`` exists to answer. The JSON library's
  ``source_version`` field caught five genuine citation defects; measured on
  2026-08-30, it was also a byte-identical copy of ``source`` in 104 of its 119
  items and carried no version token whatsoever in 50 of them. So this check is
  **stricter than the field it replaces**, not a degradation of it -- a required
  field is not a pin.
* **At most 20 checkbox items per file.** The file is the unit an agent loads, so
  file size *is* the token budget. Enforcing the ceiling is what makes splitting
  by *when it applies* the natural move instead of growing one file forever.

Plus the ``fable`` grep: Fable bills usage credits on a Pro subscription
(``.claude/rules/repo-conventions.md``), so it must not appear anywhere an agent
could read it as a suggestion.

:class:`NegativeControls` runs every one of these checks against deliberately
malformed synthetic files. A shape test that has quietly stopped detecting
anything fails there rather than passing forever -- and gate 2 requires exactly
that demonstration before the format is trusted.

**Scope, stated because it is the obvious hole.** Only *checklist* files are held
to the full shape: ``golden-rules/<domain>/<file>.md``. The three top-level
documents (``README.md``, ``AUTHORING-GUIDE.md``, ``GROWTH.md``) are prose
contracts, not checklists an agent loads per task; they are held to the ``fable``
grep and, where they carry a ``Status:`` line at all, to its format. Nothing here
checks whether an item is *good*. It checks that the file has not stopped being
the format it claims to be.
"""

import re
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = REPO_ROOT / "golden-rules"

#: The ceiling from ``AUTHORING-GUIDE.md``. The number is a judgement; the
#: enforcement is not. Raising it is a decision to be argued for here, in one
#: place, rather than absorbed one file at a time.
MAX_CHECKBOX_ITEMS = 20

#: Exactly two forms, per ``README.md``. Anchored whole-line: a trailing
#: qualifier ("ratified 2026-08-30, mostly") is a third form wearing the costume
#: of the first.
STATUS_RE = re.compile(
    r"^Status: (?:ratified (?P<ratified>\d{4}-\d{2}-\d{2})"
    r"|drafted by orchestrator (?P<drafted>\d{4}-\d{2}-\d{2}), unreviewed)$"
)

#: What counts as a version pin. Any one of: an ISO date (`2026-08-30`), a bare
#: year (`(2014)`, `29148:2018`), a dotted version (`5.0.0`, `v2.1.221`), or an
#: edition (`2nd ed.`). Crude on purpose -- it cannot tell a real citation from a
#: plausible one, and does not pretend to. What it does catch is the citation
#: that names an authority and no version at all, which is the shape 50 of the
#: old library's 119 items had.
VERSION_PIN_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b"
    r"|\b(?:19|20)\d{2}\b"
    r"|\bv?\d+\.\d+(?:\.\d+)?\b"
    r"|\b\d+(?:st|nd|rd|th) ed\.",
)

SOURCES_LINE_RE = re.compile(r"^Sources?:")
CHECKBOX_RE = re.compile(r"^\s*- \[[ xX]\]")
GROUP_HEADING_RE = re.compile(r"^## ")
FABLE_RE = re.compile(r"\bfable\b", re.IGNORECASE)

FENCE_RE = re.compile(r"^```")


def strip_fences(text):
    """Blank out fenced code blocks, keeping line numbering intact.

    ``README.md`` documents the format by *showing* a specimen file, fences and
    all. Without this, the library's own documentation trips every check it
    documents -- and the fix a reader would reach for is to weaken the check.
    """
    out, inside = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            inside = not inside
            out.append("")
            continue
        out.append("" if inside else line)
    return "\n".join(out)


def checklist_files():
    """Every checklist file: ``golden-rules/<domain>/<file>.md``."""
    if not GOLDEN_ROOT.is_dir():
        return []
    return sorted(p for p in GOLDEN_ROOT.glob("*/*.md") if p.is_file())


def document_files():
    """Every markdown file under ``golden-rules/``, checklists included."""
    if not GOLDEN_ROOT.is_dir():
        return []
    return sorted(p for p in GOLDEN_ROOT.rglob("*.md") if p.is_file())


# --------------------------------------------------------------------------
# The checks. Each returns a list of human-readable problems, empty when clean.
# Factored out so :class:`NegativeControls` exercises the same code the real
# corpus is judged by, rather than a re-implementation that could drift from it.
# --------------------------------------------------------------------------

def status_problems(text, today=None):
    """The file carries exactly one well-formed, non-future ``Status:`` line."""
    today = today or date.today()
    body = strip_fences(text)
    lines = [line for line in body.splitlines() if line.startswith("Status:")]
    if not lines:
        return ["no `Status:` line"]
    if len(lines) > 1:
        return ["{} `Status:` lines; expected exactly one".format(len(lines))]

    match = STATUS_RE.match(lines[0])
    if not match:
        return ["`Status:` is not one of the two permitted forms: "
                + repr(lines[0])]

    stamp = match.group("ratified") or match.group("drafted")
    try:
        stamped = date.fromisoformat(stamp)
    except ValueError:
        return ["`Status:` date is not a real date: " + stamp]
    if stamped > today:
        return ["`Status:` date is in the future: {} > {}".format(stamped, today)]
    return []


def group_problems(text):
    """Each ``##`` group has exactly one ``Sources:`` line, and it is pinned."""
    body = strip_fences(text)
    problems = []
    groups, current, heading = [], None, None
    for line in body.splitlines():
        if GROUP_HEADING_RE.match(line):
            if current is not None:
                groups.append((heading, current))
            heading, current = line.strip(), []
            continue
        if current is not None:
            current.append(line)
    if current is not None:
        groups.append((heading, current))

    if not groups:
        return ["no `##` groups"]

    for heading, block in groups:
        starts = [i for i, line in enumerate(block)
                  if SOURCES_LINE_RE.match(line)]
        if len(starts) != 1:
            problems.append("{}: {} `Sources:` lines; expected exactly one"
                            .format(heading, len(starts)))
            continue
        # The citation wraps: take the Sources line and everything after it, so
        # a version sitting on a continuation line still counts.
        citation = "\n".join(block[starts[0]:])
        if not VERSION_PIN_RE.search(citation):
            problems.append(
                "{}: `Sources:` carries no version pin -- no date, year, "
                "dotted version or edition".format(heading))
    return problems


def size_problems(text, ceiling=MAX_CHECKBOX_ITEMS):
    """The file stays under the checkbox ceiling."""
    body = strip_fences(text)
    count = sum(1 for line in body.splitlines() if CHECKBOX_RE.match(line))
    if count == 0:
        return ["no checkbox items"]
    if count > ceiling:
        return ["{} checkbox items; ceiling is {} -- split the file by when "
                "each group applies".format(count, ceiling)]
    return []


def fable_problems(text):
    """``fable`` appears nowhere an agent could read it as a suggestion."""
    hits = [n for n, line in enumerate(text.splitlines(), start=1)
            if FABLE_RE.search(line)]
    if hits:
        return ["`fable` named on line(s) " + ", ".join(str(n) for n in hits)]
    return []


# --------------------------------------------------------------------------
# The corpus
# --------------------------------------------------------------------------

class CorpusNotEmpty(unittest.TestCase):
    """Every check below iterates a directory, and an empty one passes them all.

    Stage 1 of the migration added this assertion to every directory-iterating
    test in the suite for exactly that reason. A new test file gets it on the
    first commit, not after the vacuous pass is discovered.
    """

    def test_the_library_exists(self):
        self.assertTrue(GOLDEN_ROOT.is_dir(),
                        "golden-rules/ is missing entirely")

    def test_checklist_files_are_present(self):
        self.assertTrue(checklist_files(),
                        "no golden-rules/<domain>/*.md files found -- every "
                        "shape test below would pass over an empty corpus")

    def test_the_contract_documents_are_present(self):
        for name in ("README.md", "AUTHORING-GUIDE.md", "GROWTH.md"):
            with self.subTest(document=name):
                self.assertTrue((GOLDEN_ROOT / name).is_file(),
                                name + " is missing")


class ChecklistShape(unittest.TestCase):
    """The three properties, over every checklist file."""

    def test_status_is_one_of_the_two_forms_with_a_real_past_date(self):
        for path in checklist_files():
            with self.subTest(path=path.relative_to(REPO_ROOT).as_posix()):
                problems = status_problems(path.read_text(encoding="utf-8"))
                self.assertEqual([], problems, "; ".join(problems))

    def test_every_group_carries_one_version_pinned_sources_line(self):
        for path in checklist_files():
            with self.subTest(path=path.relative_to(REPO_ROOT).as_posix()):
                problems = group_problems(path.read_text(encoding="utf-8"))
                self.assertEqual([], problems, "; ".join(problems))

    def test_no_file_exceeds_the_checkbox_ceiling(self):
        for path in checklist_files():
            with self.subTest(path=path.relative_to(REPO_ROOT).as_posix()):
                problems = size_problems(path.read_text(encoding="utf-8"))
                self.assertEqual([], problems, "; ".join(problems))


class ContractDocuments(unittest.TestCase):
    """The top-level prose documents, held to what applies to prose."""

    def test_a_status_line_if_present_is_well_formed(self):
        for name in ("README.md", "AUTHORING-GUIDE.md", "GROWTH.md"):
            path = GOLDEN_ROOT / name
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            # A *line* beginning `Status:`, not the substring -- README.md has a
            # section heading `## \`Status:\` — exactly two forms` that describes
            # the stamp without carrying one.
            if not any(line.startswith("Status:")
                       for line in strip_fences(text).splitlines()):
                continue
            with self.subTest(document=name):
                problems = status_problems(text)
                self.assertEqual([], problems, "; ".join(problems))


class ModelRoster(unittest.TestCase):
    """Fable bills usage credits on a Pro subscription, so it is never suggested.

    The constraint is recorded in ``.claude/rules/repo-conventions.md`` and named
    in the migration plan. It is greppable, so it is grepped.
    """

    def test_the_corpus_is_not_empty(self):
        self.assertTrue(document_files(), "no markdown found under golden-rules/")

    def test_fable_is_named_nowhere(self):
        for path in document_files():
            with self.subTest(path=path.relative_to(REPO_ROOT).as_posix()):
                problems = fable_problems(path.read_text(encoding="utf-8"))
                self.assertEqual([], problems, "; ".join(problems))


class NegativeControls(unittest.TestCase):
    """Every check, run against a file built to break exactly that check.

    Gate 2 of ``plans/golden-rules-migration.md`` requires this: *"New tests
    pass, and fail when fed a deliberately malformed rule file."* A check nobody
    has watched fail is a check nobody has tested.
    """

    WELL_FORMED = (
        "# Example — golden rules\n"
        "\n"
        "Status: ratified 2026-08-29\n"
        "Applies when demonstrating the format.\n"
        "\n"
        "## Before doing the thing\n"
        "\n"
        "- [ ] Do the checkable thing — because otherwise the observable failure.\n"
        "\n"
        "Sources: Pro Git, 2nd ed. (Chacon & Straub, 2014) ch.3.\n"
    )

    def test_the_well_formed_control_passes_every_check(self):
        # Without this the negative controls below prove nothing: a check that
        # rejects *everything* also rejects every malformed file.
        text = self.WELL_FORMED
        self.assertEqual([], status_problems(text, today=date(2026, 8, 30)))
        self.assertEqual([], group_problems(text))
        self.assertEqual([], size_problems(text))
        self.assertEqual([], fable_problems(text))

    def test_a_missing_status_line_is_caught(self):
        text = self.WELL_FORMED.replace("Status: ratified 2026-08-29\n", "")
        self.assertTrue(status_problems(text, today=date(2026, 8, 30)))

    def test_a_third_status_form_is_caught(self):
        text = self.WELL_FORMED.replace("Status: ratified 2026-08-29",
                                        "Status: probably fine, ask Dave")
        self.assertTrue(status_problems(text, today=date(2026, 8, 30)))

    def test_a_status_form_with_a_trailing_qualifier_is_caught(self):
        text = self.WELL_FORMED.replace("Status: ratified 2026-08-29",
                                        "Status: ratified 2026-08-29, mostly")
        self.assertTrue(status_problems(text, today=date(2026, 8, 30)))

    def test_an_undated_status_line_is_caught(self):
        text = self.WELL_FORMED.replace("Status: ratified 2026-08-29",
                                        "Status: ratified")
        self.assertTrue(status_problems(text, today=date(2026, 8, 30)))

    def test_a_future_status_date_is_caught(self):
        text = self.WELL_FORMED.replace("2026-08-29", "2099-01-01")
        self.assertTrue(status_problems(text, today=date(2026, 8, 30)))

    def test_an_impossible_status_date_is_caught(self):
        text = self.WELL_FORMED.replace("2026-08-29", "2026-02-31")
        self.assertTrue(status_problems(text, today=date(2026, 8, 30)))

    def test_a_group_with_no_sources_line_is_caught(self):
        text = self.WELL_FORMED.replace(
            "Sources: Pro Git, 2nd ed. (Chacon & Straub, 2014) ch.3.\n", "")
        self.assertTrue(group_problems(text))

    def test_a_group_with_two_sources_lines_is_caught(self):
        text = self.WELL_FORMED + "Sources: something else, 2020.\n"
        self.assertTrue(group_problems(text))

    def test_an_unpinned_citation_is_caught(self):
        # This is the gate-2 criterion itself: the shape the old library had in
        # 50 of its 119 items -- an authority named, no version anywhere.
        text = self.WELL_FORMED.replace(
            "Sources: Pro Git, 2nd ed. (Chacon & Straub, 2014) ch.3.",
            "Sources: Pro Git.")
        problems = group_problems(text)
        self.assertTrue(problems)
        self.assertIn("version pin", " ".join(problems))

    def test_the_honest_first_principles_fallback_is_accepted(self):
        # The fallback must stay easy, or the incentive is to invent a citation.
        text = self.WELL_FORMED.replace(
            "Sources: Pro Git, 2nd ed. (Chacon & Straub, 2014) ch.3.",
            "Sources: reasoned from first principles, 2026-08-30.")
        self.assertEqual([], group_problems(text))

    def test_an_undated_first_principles_line_is_caught(self):
        text = self.WELL_FORMED.replace(
            "Sources: Pro Git, 2nd ed. (Chacon & Straub, 2014) ch.3.",
            "Sources: reasoned from first principles.")
        self.assertTrue(group_problems(text))

    def test_a_file_over_the_ceiling_is_caught(self):
        bloat = "\n".join("- [ ] item {}".format(n) for n in range(30))
        text = self.WELL_FORMED.replace(
            "- [ ] Do the checkable thing — because otherwise the observable "
            "failure.", bloat)
        problems = size_problems(text)
        self.assertTrue(problems)
        self.assertIn("ceiling", " ".join(problems))

    def test_a_file_with_no_checkboxes_is_caught(self):
        text = self.WELL_FORMED.replace(
            "- [ ] Do the checkable thing — because otherwise the observable "
            "failure.", "Just some prose.")
        self.assertTrue(size_problems(text))

    def test_a_named_fable_model_is_caught(self):
        text = self.WELL_FORMED + "\nUse model: fable for this domain.\n"
        self.assertTrue(fable_problems(text))

    def test_the_ticked_checkbox_form_still_counts(self):
        # A project layer arrives with items already ticked. If `- [x]` did not
        # count, a file could sail past the ceiling simply by being used.
        text = self.WELL_FORMED.replace("- [ ]", "- [x]")
        self.assertEqual([], size_problems(text))

    def test_a_fenced_specimen_does_not_trip_the_checks(self):
        # README.md documents the format by showing one. If fences were scanned,
        # the library's own documentation would fail the checks it documents --
        # and the tempting fix is to weaken the check.
        text = ("# Doc\n\nStatus: ratified 2026-08-29\n\n## A group\n\n"
                "- [ ] one real item — with its reason.\n\n"
                "```markdown\n"
                "Status: whatever you like\n"
                "## A specimen group with no sources at all\n"
                "```\n\n"
                "Sources: reasoned from first principles, 2026-08-30.\n")
        self.assertEqual([], status_problems(text, today=date(2026, 8, 30)))
        self.assertEqual([], group_problems(text))

    def test_the_corpus_walk_finds_nothing_in_an_empty_tree(self):
        # Proves CorpusNotEmpty above is load-bearing rather than decorative:
        # over an empty tree the walk really does return nothing, so without
        # that class every shape test would pass by examining zero files.
        with TemporaryDirectory() as scratch:
            empty = Path(scratch) / "golden-rules"
            empty.mkdir()
            self.assertEqual([], sorted(empty.glob("*/*.md")))


if __name__ == "__main__":
    unittest.main()
