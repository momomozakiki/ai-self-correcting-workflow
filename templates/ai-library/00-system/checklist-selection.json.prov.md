---
title: Provenance — checklist-selection.json
version: 1.0
last_validated: 2026-08-05
official: false
source: agent-generated
tags: [provenance, checklist, selection, governance]
applies_when: "Checking where the checklist loading table came from and what it is allowed to claim."
estimated_tokens: 300
---

# Provenance — `checklist-selection.json`

## What it is

The one table deciding which checklists load, for both `.ai/03-planning/` (Phase 1,
reviews the plan) and `.ai/05-domains/` (Phase 2, reviews the code).

## Where it came from

Extracted on 2026-08-05 from `.ai/05-domains/manifest.json`, where the `selection` block
had lived since the checklist system was adopted. Nothing about the table changed in the
move except the addition of the `phases` block; `task_sizes`, `task_size_is_declared` and
`contexts` are carried over verbatim.

## Why it moved

Plan-review checklists arrived and needed selecting too. Leaving the table in
`05-domains/manifest.json` and adding a second one to `03-planning/manifest.json` would
have created two definitions of one thing — the drift this library exists to prevent, and
the same objection already recorded against restating the loading logic inside each skill.
A domain manifest cannot be the authority on a folder it does not contain.

## What it does not claim

`enforcement_status` is `convention`, and the note says why: loading happens at prompt
time inside the agent's reasoning, where no hook runs. `ChecklistSelection` in
`tests/test_governance_library.py` checks that the table is internally consistent — every
category named has a rule file, every rule is reachable from some phase, no rule gates on
a task size outside the closed vocabulary. It cannot check that the table was consulted.

## Related

- `.ai/03-planning/manifest.json`, `.ai/05-domains/manifest.json` — indexes, not second opinions
- `docs/checklist-system.md` — the canonical description of the whole system
- `skills/adaptive-workflow/SKILL.md`, `skills/autonomous-task/SKILL.md` — both read this file
