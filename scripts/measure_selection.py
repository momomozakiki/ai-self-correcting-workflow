#!/usr/bin/env python3
"""Re-derive how many checklist items `.ai/00-system/checklist-selection.json` loads.

    python scripts/measure_selection.py

`golden-rules/README.md` states that the old JSON library loaded 9 items for a
typo fix and 34 for a REST API, and uses those figures to argue that the markdown
format is a token-budget regression at small task sizes. Those are load-bearing
numbers in a live argument, so they must be re-derivable by anyone rather than
taken on the say-so of whoever ran it once.

This script exists because the plan-review item *"is every count and measurement
in the plan reproducible by a command?"* was worked against
`plans/golden-rules-migration.md` on 2026-08-31 and returned a **finding**: these
figures had been produced by a throwaway script and never committed. The item
caught its own author, which is the most useful thing it could have done.

Selection rule, quoted from the config: *"Load a checklist rule when its
workflow_phase matches the phase you are in AND its task_size_required contains
the declared task size AND (its tech_stack_required is empty OR intersects the
project's stack). Within Phase 2, `contexts` narrows further."*

Stdlib only, per `.claude/rules/repo-conventions.md`.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LIBRARY = REPO_ROOT / ".ai"
SELECTION = LIBRARY / "00-system" / "checklist-selection.json"

SIZES = ("typo_fix", "small_change", "new_module", "major_refactor")
FOLDERS = ("03-planning", "05-domains")


def load_rules():
    rules = []
    for folder in FOLDERS:
        for path in sorted((LIBRARY / folder).glob("rule-*.json")):
            rules.append(json.loads(path.read_text(encoding="utf-8")))
    return rules


def count(rules, phase, size, categories=None):
    """Items loaded at ``phase`` for ``size``, optionally narrowed by context."""
    total = 0
    for rule in rules:
        if str(rule.get("workflow_phase")) != str(phase):
            continue
        if size not in rule.get("task_size_required", []):
            continue
        if categories is not None and rule.get("category") not in categories:
            continue
        total += len(rule["checklist"])
    return total


def main(argv=None):
    if not SELECTION.is_file():
        print("no {} -- `.ai/` has been retired; these figures are historical "
              "and live in golden-rules/README.md".format(
                  SELECTION.relative_to(REPO_ROOT).as_posix()))
        return 0

    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    rules = load_rules()
    items = sum(len(r["checklist"]) for r in rules)
    print("{} rule files, {} items total\n".format(len(rules), items))

    for phase in ("1", "2"):
        row = "  ".join("{} {}".format(s, count(rules, phase, s)) for s in SIZES)
        print("Phase {} by task size: {}".format(phase, row))

    print("\nPhase 2 at new_module, narrowed by context:")
    contexts = selection.get("contexts", {})
    for name, categories in sorted(
            contexts.items(), key=lambda kv: count(rules, "2", "new_module", kv[1])):
        print("  {:<16} {}".format(name, count(rules, "2", "new_module", categories)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
