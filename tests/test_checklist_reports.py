#!/usr/bin/env python3
"""Shape tests for worked-checklist reports under ``plans/*/checklists/``.

Stdlib ``unittest`` only -- run with::

    python -m unittest discover -s tests
    # or
    python -m unittest tests.test_checklist_reports

Until 2026-08-31 the checklist-execution contract was prose -- *"report the
answers, including the ones that pass… an absent answer is the finding"* -- and
**nothing anywhere checked that any answer was ever given**. A skipped item and a
passed item were indistinguishable, because both looked like silence.
``ROADMAP.md`` pre-registered the gap and guessed it might be unenforceable via a
hook, which is correct: checklist *loading* happens inside model reasoning, where
no hook runs. But the *report* is a file, and a file can be reconciled.

**What is checked here, and what is checked elsewhere.** This module holds the
properties that are true at any moment: the verdict vocabulary, one line per
golden item in order, the two-zone boundary, required reasons, the ``Status:``
match, and that every declared checklist has a report. Whether every item has
been *answered* is a **closure** property, and it lives in
``scripts/checklist_status.py`` instead.

That split is deliberate and was the correction that reshaped this design. An
outstanding ``todo`` is the normal state of a task in progress. Rejecting it here
would leave the suite red for the whole duration of every task -- destroying the
meaning of a red suite, and creating pressure to fill verdicts early to get back
to green. That is *mark-then-do*: fabrication, the one failure neither check can
detect. A design that rewards its own blind spot is worse than one that admits
it.

**The two-zone split is the safety property.** The verdict block carries exactly
the golden file's items; ``## Working notes`` below it is the agent's own and is
never counted. An agent that could add lines to the block deciding whether it is
finished could always reach "finished" -- ``docs/RETROSPECTIVE.md``: *"a test
that can be satisfied by adjusting the data it measures is not a test."* The
block is therefore reconciled against the golden file itself, not against a
stored snapshot that could be edited too.

:class:`NegativeControls` runs every check against deliberately malformed
reports, including the two halves of the mutable-measuring-stick failure -- a
line added and a line removed -- both of which must fail *while the file still
looks well-formed*. It also asserts that a large Working-notes section
**passes**, because a check that punished growth there would push emergent work
back into the counted zone and rebuild the very problem.

**What none of this catches**, stated because a check whose limits are unstated
gets read as covering more than it does: fabrication (write ``pass`` everywhere
without looking and it all goes green), avoidance (the ``Checklists:`` line is
self-declared, and ``none — trivial`` passes), a reason that says nothing, and an
edited golden base. See ``golden-rules/REPORTING.md``.
"""

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import checklist_report as cr  # noqa: E402

WELL_FORMED_GOLDEN = (
    "# Example — golden rules\n"
    "\n"
    "Status: ratified 2026-08-29\n"
    "Applies when demonstrating the format.\n"
    "\n"
    "## Before doing the thing\n"
    "\n"
    "- [ ] First checkable thing — with its reason.\n"
    "- [ ] Second checkable thing — with its reason.\n"
    "\n"
    "Sources: Pro Git, 2nd ed. (Chacon & Straub, 2014) ch.3.\n"
)

WELL_FORMED_REPORT = (
    "# Checklist report — example/demo.md\n"
    "\n"
    "Golden: golden-rules/example/demo.md\n"
    "Status: ratified 2026-08-29\n"
    "Worked: 2026-08-31 against plans/demo.md\n"
    "\n"
    "- pass | First checkable thing\n"
    "- finding | Second checkable thing | it does not hold at foo.py:12\n"
    "\n"
    "## Working notes\n"
    "\n"
    "- some free-form note\n"
)


class Scratch:
    """A throwaway repo layout, so controls never touch the real tree.

    ``checklist_report`` resolves paths from module-level roots, so they are
    repointed for the duration and restored afterwards. Without the restore, one
    negative control would silently redirect every later test.
    """

    def __init__(self, golden=WELL_FORMED_GOLDEN, report=WELL_FORMED_REPORT):
        self.golden_text, self.report_text = golden, report

    def __enter__(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self._saved = (cr.REPO_ROOT, cr.GOLDEN_ROOT, cr.PLANS_ROOT)

        golden = root / "golden-rules" / "example" / "demo.md"
        golden.parent.mkdir(parents=True)
        golden.write_text(self.golden_text, encoding="utf-8")

        report = root / "plans" / "demo" / "checklists" / "example" / "demo.md"
        report.parent.mkdir(parents=True)
        report.write_text(self.report_text, encoding="utf-8")

        cr.REPO_ROOT = root
        cr.GOLDEN_ROOT = root / "golden-rules"
        cr.PLANS_ROOT = root / "plans"
        self.report_path = report
        return self

    def __exit__(self, *exc):
        cr.REPO_ROOT, cr.GOLDEN_ROOT, cr.PLANS_ROOT = self._saved
        self._tmp.cleanup()
        return False

    def problems(self):
        return cr.reconcile(cr.Report(self.report_path))


class CorpusNotEmpty(unittest.TestCase):
    """Every check below iterates a directory, and an empty one passes them all.

    Stage 1 of the golden-rules migration added this assertion to every
    directory-iterating test in the suite. A new test file gets it on the first
    commit, not after the vacuous pass is discovered.
    """

    def test_the_format_contract_exists(self):
        self.assertTrue((REPO_ROOT / "golden-rules" / "REPORTING.md").is_file(),
                        "golden-rules/REPORTING.md is missing -- the format "
                        "these tests enforce would be undocumented")

    def test_task_plans_are_present(self):
        self.assertTrue(cr.plan_files(),
                        "no task plans under plans/ -- DeclaredChecklists "
                        "would pass by examining nothing")


class DeclaredChecklists(unittest.TestCase):
    """Every plan declares what it owes, and every declared file has a report.

    This is what stops the whole layer passing over nothing: without a mandatory
    declaration, a task that writes no report at all is indistinguishable from
    one that owed none.
    """

    def test_every_plan_declares_its_checklists(self):
        for plan in cr.plan_files():
            with self.subTest(plan=plan.name):
                _, _, raw = cr.declared_checklists(plan)
                self.assertIsNotNone(
                    raw,
                    "no `Checklists:` line. Declaring nothing is a decision and "
                    "is written as one: `Checklists: none — <reason>`")

    def test_a_declared_none_carries_a_reason(self):
        for plan in cr.plan_files():
            _, declared_none, raw = cr.declared_checklists(plan)
            if not declared_none:
                continue
            with self.subTest(plan=plan.name):
                self.assertRegex(
                    raw, r"none\s*[—-]\s*\S",
                    "`Checklists: none` needs a reason after an em dash")

    def test_every_declared_checklist_has_a_report(self):
        for plan in cr.plan_files():
            declared, _, _ = cr.declared_checklists(plan)
            for rel in declared:
                with self.subTest(plan=plan.name, checklist=rel):
                    report = cr.report_path_for(plan, rel)
                    self.assertTrue(
                        report.is_file(),
                        "declared but absent: expected a report at "
                        + report.relative_to(REPO_ROOT).as_posix())

    def test_every_declared_checklist_names_a_real_golden_file(self):
        for plan in cr.plan_files():
            declared, _, _ = cr.declared_checklists(plan)
            for rel in declared:
                with self.subTest(plan=plan.name, checklist=rel):
                    self.assertTrue((cr.GOLDEN_ROOT / rel).is_file(),
                                    "no golden file at golden-rules/" + rel)


class ReportShape(unittest.TestCase):
    """Every report on disk reconciles with its golden file."""

    def test_every_report_is_well_formed(self):
        for path in cr.report_files():
            with self.subTest(report=path.relative_to(REPO_ROOT).as_posix()):
                problems = cr.reconcile(cr.Report(path))
                self.assertEqual([], problems, "; ".join(problems))


class NegativeControls(unittest.TestCase):
    """Every check, against a report built to break exactly that check.

    Per ``docs/RETROSPECTIVE.md``: *"a negative control names the test, or it is
    not a control."* Each case asserts on the specific problem, not merely that
    something failed.
    """

    def test_the_well_formed_control_passes(self):
        # Without this the controls below prove nothing: a checker that rejects
        # everything also rejects every malformed report.
        with Scratch() as scratch:
            self.assertEqual([], scratch.problems())

    def test_a_line_added_to_the_verdict_block_is_caught(self):
        # Half one of the mutable-measuring-stick failure. The file still looks
        # perfectly well-formed, which is exactly why a shape-only check misses
        # it and reconciliation against the golden file does not.
        broken = WELL_FORMED_REPORT.replace(
            "\n\n## Working notes",
            "\n- pass | An item I invented\n\n## Working notes")
        with Scratch(report=broken) as scratch:
            problems = scratch.problems()
            self.assertTrue(problems)
            self.assertIn("added or removed", " ".join(problems))

    def test_a_line_removed_from_the_verdict_block_is_caught(self):
        broken = WELL_FORMED_REPORT.replace("- pass | First checkable thing\n", "")
        with Scratch(report=broken) as scratch:
            problems = scratch.problems()
            self.assertTrue(problems)
            self.assertIn("added or removed", " ".join(problems))

    def test_a_large_working_notes_section_still_passes(self):
        # Growth there is the intended behaviour. A check that punished it would
        # push emergent work back into the counted zone and rebuild the problem.
        noisy = WELL_FORMED_REPORT + "\n".join(
            "- discovered step {}".format(n) for n in range(50))
        with Scratch(report=noisy) as scratch:
            self.assertEqual([], scratch.problems())

    def test_an_unknown_verdict_is_caught(self):
        broken = WELL_FORMED_REPORT.replace("- pass |", "- mostly fine |")
        with Scratch(report=broken) as scratch:
            problems = scratch.problems()
            self.assertTrue(problems)
            self.assertIn("unknown verdict", " ".join(problems))

    def test_a_stale_status_is_caught(self):
        # The golden file moved on; the report answers a different version.
        moved = WELL_FORMED_GOLDEN.replace("Status: ratified 2026-08-29",
                                           "Status: ratified 2026-08-31")
        with Scratch(golden=moved) as scratch:
            problems = scratch.problems()
            self.assertTrue(problems)
            self.assertIn("different version", " ".join(problems))

    def test_a_finding_without_a_reason_is_caught(self):
        broken = WELL_FORMED_REPORT.replace(
            "- finding | Second checkable thing | it does not hold at foo.py:12",
            "- finding | Second checkable thing")
        with Scratch(report=broken) as scratch:
            problems = scratch.problems()
            self.assertTrue(problems)
            self.assertIn("needs a reason", " ".join(problems))

    def test_an_n_a_without_a_reason_is_caught(self):
        broken = WELL_FORMED_REPORT.replace(
            "- finding | Second checkable thing | it does not hold at foo.py:12",
            "- n/a | Second checkable thing")
        with Scratch(report=broken) as scratch:
            self.assertTrue(scratch.problems())

    def test_a_todo_needs_no_reason_and_passes_the_shape_check(self):
        # The correction that reshaped this design: outstanding work is the
        # normal in-flight state and must not fail the suite.
        in_flight = WELL_FORMED_REPORT.replace(
            "- finding | Second checkable thing | it does not hold at foo.py:12",
            "- todo | Second checkable thing")
        with Scratch(report=in_flight) as scratch:
            self.assertEqual([], scratch.problems())
            outstanding = cr.Report(scratch.report_path).outstanding()
            self.assertEqual(1, len(outstanding),
                             "the closure gate must still see it as outstanding")

    def test_a_missing_notes_heading_is_caught(self):
        broken = WELL_FORMED_REPORT.replace("## Working notes\n", "")
        with Scratch(report=broken) as scratch:
            problems = scratch.problems()
            self.assertTrue(problems)
            self.assertIn("Working notes", " ".join(problems))

    def test_a_golden_field_disagreeing_with_the_path_is_caught(self):
        broken = WELL_FORMED_REPORT.replace(
            "Golden: golden-rules/example/demo.md",
            "Golden: golden-rules/somewhere/else.md")
        with Scratch(report=broken) as scratch:
            problems = scratch.problems()
            self.assertTrue(problems)
            self.assertIn("mirrors", " ".join(problems))

    def test_a_report_with_no_golden_file_is_caught(self):
        with Scratch() as scratch:
            (cr.GOLDEN_ROOT / "example" / "demo.md").unlink()
            problems = scratch.problems()
            self.assertTrue(problems)
            self.assertIn("no golden file", " ".join(problems))

    def test_the_skeleton_generator_produces_a_well_formed_report(self):
        # The skeleton is what an agent starts from. If it did not itself pass,
        # every task would begin with a failing suite.
        with Scratch() as scratch:
            golden = cr.GOLDEN_ROOT / "example" / "demo.md"
            plan = cr.PLANS_ROOT / "demo.md"
            text = cr.skeleton(golden, plan, "2026-08-31")
            scratch.report_path.write_text(text, encoding="utf-8")
            self.assertEqual([], scratch.problems())
            self.assertEqual(2, len(cr.Report(scratch.report_path).outstanding()))


if __name__ == "__main__":
    unittest.main()
