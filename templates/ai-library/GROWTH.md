---
title: Growing the governance library
version: 1.1
last_validated: 2026-08-04
official: false
source: agent-generated
tags: [governance, growth, retrospective, self-hardening]
applies_when: "Adding a rule, domain, or blueprint to the library after a retrospective."
estimated_tokens: 400
---

# Growing this library

Seeded empty rather than pre-filled. A rule that nobody hit yet is a guess; a rule harvested
from a real mistake is knowledge. The library grows through three protocols, all triggered
from the Phase 3 retrospective.

## Breadth - a new domain folder
A task needed a domain with no rules at all. Create `05-domains/<domain>/`, add a
`manifest.json`, and write the rules you actually needed. Do not speculate beyond them.

## Depth - a new rule in an existing folder
An edge case bit you inside a domain that already exists. Add one rule file. Update the
folder's `manifest.json` in the same edit - a manifest that lies is worse than no manifest.

## Blueprint refinement
A human corrected a component choice. Update the blueprint's mutable variables so the next
task starts from the corrected version.

## The self-hardening rule
A mistake recorded **twice** in `docs/RETROSPECTIVE.md` stops being a note and becomes
structure: a checklist item in `skills/adaptive-workflow/SKILL.md` and a rule file under
`01-phases/`. `--self-test` reports recurring entries that have not yet been codified;
reaching maturity level 5 requires that none are outstanding.

## Every new rule file needs
`id`, `enforcement`, `enforcement_status` (live | convention | declarative), `risk_source`,
`risk_weight`, and a `provenance` block.

`risk_source` is one of the CISA five, each defined over a weight band
(`docs/self-growing-checklist-ecosystem/03-risk-gates-and-metrics.md` §11.3):

| `risk_source` | What it covers | `risk_weight` |
|---|---|---|
| `component` | vulnerabilities in tools, APIs, data sources | 1-3 |
| `design` | flaws in planning, reasoning, or action logic | 4-6 |
| `capability` | risks from autonomous action execution | 7-10 |
| `structural` | composition and interaction of multiple agents | 6-9 |
| `accountability` | unclear or diffused responsibility | 8-10 |

If your honest weight falls outside its band, **do not move the number**. Add a
`risk_weight_note` saying why the imported band does not fit here. The bands were written
for an agent fleet; some of them do not transfer to a single-operator repo, and fitting a
number to a threshold is the same failure as claiming enforcement you do not have.

If you cannot name which hook or test makes it *live*, it is not live - say `convention`,
give it an `enforcement_note` saying what the real mechanism is, and mean it. A `live`
artifact carries `enforced_by`: a list of `path::symbol` references that
`tests/test_governance_library.py` resolves against the actual source. A tier claim that
cannot be traced to code fails the build.
