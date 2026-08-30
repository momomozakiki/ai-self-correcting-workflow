#!/usr/bin/env python3
"""Evidence for `GROWTH.md`, harvested from worked checklist reports.

    python scripts/checklist_growth.py

`GROWTH.md` has always said an item that never applies is a strike candidate.
Until reports existed that was somebody's impression. A corpus of reports makes
it countable, and each of GROWTH's criteria has a signal here:

===========================  =================================================
Signal across reports        Evidence of
===========================  =================================================
repeatedly `cannot tell      **Unanswerable** -- a strike criterion. Nobody can
from here`                   tell whether it passed, so it has been ticked
                             without being checked
repeatedly `n/a`             Its condition never fires. Either the group's
                             *when* is wrong or the item belongs in a narrower
                             file
always `pass`                **Nothing.** Explicitly not a strike -- a rule that
                             prevents failures produces no failures
===========================  =================================================

**Three things this deliberately does not do.**

It never strikes anything. It prints candidates for a human to rule on, because
that is what `GROWTH.md` already requires -- *"Drift is reported for human
ratification instead."* An agent that both applies a rule and decides its fate is
the loop `docs/checklist-system.md` records as dropped for having no ground truth
anywhere in it.

It sets no threshold. A number to clear is a number to game, and
`docs/RETROSPECTIVE.md` already carries an entry about an item's data being
nudged to satisfy a validator.

It prints the reason strings, not just the tallies. `n/a` is the cheapest verdict
to write, so a pile of them may mean the item is wrong *or* that someone was
avoiding work -- and those are identical in a count. Only the reasons tell them
apart, so only a human can.

Always exits 0. This reports; it does not gate.

Stdlib only, per `.claude/rules/repo-conventions.md`.
"""

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import checklist_report as cr  # noqa: E402

#: Verdicts worth surfacing as evidence, and what each suggests. `pass` is
#: absent on purpose: see the module docstring and GROWTH.md's inverted-strike
#: warning. Adding it here would rebuild the exact mistake that document exists
#: to prevent.
SIGNALS = {
    "cannot tell from here": "unanswerable — strike candidate (GROWTH.md)",
    "n/a": "condition never fires — check the group's *when*",
}


def main(argv=None):
    reports = cr.report_files()
    if not reports:
        print("no reports under plans/*/checklists/ -- nothing to harvest")
        print("This is an empty corpus, not a clean bill of health.")
        return 0

    # (golden file, item index) -> verdict -> [(report, reason)]
    tally = defaultdict(lambda: defaultdict(list))
    item_text = {}
    counted = 0

    for path in reports:
        golden = cr.golden_for(path)
        if golden is None or not golden.is_file():
            continue
        report = cr.Report(path)
        if cr.reconcile(report):
            print("skipping malformed report {} -- run the suite for details"
                  .format(report.rel))
            continue
        rel_golden = golden.relative_to(cr.GOLDEN_ROOT).as_posix()
        for index, entry in enumerate(report.verdicts):
            key = (rel_golden, index)
            tally[key][entry["verdict"]].append((report.rel, entry["reason"]))
            item_text[key] = entry["item"]
        counted += 1

    print("harvested {} report(s) over {} golden item(s)\n"
          .format(counted, len(tally)))

    candidates = 0
    for key in sorted(tally):
        rel_golden, index = key
        for verdict, note in SIGNALS.items():
            occurrences = tally[key].get(verdict, [])
            if len(occurrences) < 2:
                continue  # one is an incident; two is a pattern (GROWTH.md)
            candidates += 1
            print("{}  item {}".format(rel_golden, index + 1))
            print("  {}".format(item_text.get(key, "")))
            print("  {} x `{}` — {}".format(len(occurrences), verdict, note))
            for report_rel, reason in occurrences:
                print("      {} — {}".format(report_rel, reason or "(no reason)"))
            print()

    if not candidates:
        print("no candidates. Nothing here says the library is good — only that "
              "no item has yet been unanswerable or inapplicable twice.")
    else:
        print("{} candidate(s). These are for a human to rule on. Nothing was "
              "struck, and an item that merely keeps passing is never a "
              "candidate.".format(candidates))

    print("\nPromotions come from recurring Working-notes steps, which are prose "
          "and are not tallied here — read them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
