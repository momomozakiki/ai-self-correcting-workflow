#!/usr/bin/env python3
"""The closure gate: are any checklist items still outstanding?

Run at Phase 3, beside the ledger entry and the plan archive::

    python scripts/checklist_status.py

Exits non-zero while any `todo` remains, or any declared checklist has no report.

**This is deliberately not a unit test**, and the separation is the point. An
outstanding `todo` is the *normal* state of a task in progress. Folding this into
`python -m unittest discover -s tests` would leave the suite red for the whole
duration of every task -- which destroys the meaning of a red suite, and worse,
creates pressure to fill verdicts early to get back to green. That is
*mark-then-do*: fabrication, the one failure neither this gate nor the shape test
can detect. So shape is a test and runs always; completeness is a gate and runs
at closure.

`tests/test_checklist_reports.py` holds the shape. This holds the finish line.

Stdlib only, per `.claude/rules/repo-conventions.md`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import checklist_report as cr  # noqa: E402


def main(argv=None):
    outstanding_total = 0
    missing_total = 0
    plans = cr.plan_files()

    if not plans:
        print("no task plans under plans/ -- nothing to gate")
        return 0

    for plan in plans:
        rel_plan = plan.relative_to(cr.REPO_ROOT).as_posix()
        declared, declared_none, raw = cr.declared_checklists(plan)

        if raw is None:
            print("{}: no `Checklists:` line".format(rel_plan))
            print("    Declaring nothing is a decision and is written as one: "
                  "`Checklists: none — <reason>`")
            missing_total += 1
            continue

        if declared_none:
            print("{}: declared none — {}".format(rel_plan, raw))
            continue

        for rel in declared:
            report = cr.report_path_for(plan, rel)
            if not report.is_file():
                print("{}: declares {} but no report at {}".format(
                    rel_plan, rel, report.relative_to(cr.REPO_ROOT).as_posix()))
                missing_total += 1
                continue

            parsed = cr.Report(report)
            todos = parsed.outstanding()
            if not todos:
                print("{}: {} — all {} items answered".format(
                    rel_plan, rel, len(parsed.verdicts)))
                continue

            print("{}: {} — {} of {} still outstanding".format(
                rel_plan, rel, len(todos), len(parsed.verdicts)))
            for entry in todos:
                print("    line {}: {}".format(entry["line"], entry["item"]))
            outstanding_total += len(todos)

    print()
    if outstanding_total or missing_total:
        print("NOT CLOSED — {} item(s) outstanding, {} report(s) missing"
              .format(outstanding_total, missing_total))
        return 1
    print("CLOSED — every declared checklist is fully answered")
    print("Note: this counts answers. It cannot tell a real `pass` from a "
          "fabricated one; see golden-rules/REPORTING.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
