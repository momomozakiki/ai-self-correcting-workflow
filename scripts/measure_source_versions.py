#!/usr/bin/env python3
"""Re-derive how much of `.ai/`'s `source_version` field was a real version pin.

    python scripts/measure_source_versions.py

Two figures, and the difference between them is the whole point:

* how many items have `source_version` **byte-identical to `source`** — the field
  restating its neighbour rather than adding anything;
* how many carry **no version token at all** — no year, no edition, no number.

The second is the one that bears on the migration. Gate 2 of
`plans/golden-rules-migration.md` assumes the JSON carries pins the markdown
might lose. Measured on 2026-08-30: 104 of 119 duplicated, but **50 of 119 with
no version anywhere**. Conversion cannot lose a pin that 50 items never had, and
`tests/test_golden_rules.py` enforcing a real pin makes the new format *stricter*
than the field it replaces.

A duplicated string can still be a perfectly good pin -- `OWASP ASVS 5.0.0` sits
in both fields and is fine -- which is exactly why the two numbers must be
reported separately. Quoting only the 104 overstates the case.

Committed because the plan-review item *"is every count and measurement in the
plan reproducible by a command?"* returned a finding against these very figures
on 2026-08-31: they had been produced by a throwaway script and never committed.

Stdlib only, per `.claude/rules/repo-conventions.md`.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LIBRARY = REPO_ROOT / ".ai"
FOLDERS = ("03-planning", "05-domains")

HAS_DIGIT = re.compile(r"\d")


def main(argv=None):
    if not LIBRARY.is_dir():
        print("no .ai/ -- the library has been retired; these figures are "
              "historical and recorded in golden-rules/AUTHORING-GUIDE.md")
        return 0

    total = duplicated = unpinned = 0
    unpinned_values = set()

    for folder in FOLDERS:
        for path in sorted((LIBRARY / folder).glob("rule-*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            items = data["checklist"]
            same = [i for i in items if i.get("source") == i.get("source_version")]
            bare = [i.get("source_version", "") for i in items
                    if not HAS_DIGIT.search(i.get("source_version", ""))]
            total += len(items)
            duplicated += len(same)
            unpinned += len(bare)
            unpinned_values.update(bare)
            print("{:>2}/{:<2} duplicated  {:>2} unpinned  {}".format(
                len(same), len(items), len(bare), path.name))

    print("\n{} of {} items have source_version == source".format(duplicated, total))
    print("{} of {} carry no version token at all".format(unpinned, total))
    if unpinned_values:
        print("\nCitations with no version anywhere:")
        for value in sorted(unpinned_values):
            print("  " + value)
    return 0


if __name__ == "__main__":
    sys.exit(main())
