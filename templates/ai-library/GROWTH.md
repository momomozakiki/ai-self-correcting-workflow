---
title: Growing the governance library
version: 1.4
last_validated: 2026-08-05
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

## Which folder a checklist belongs in

Two folders, two phases, and the distinction is not cosmetic:

| Folder | Phase | Reviews | Gated on tech stack? |
|---|---|---|---|
| `03-planning/` | 1 | The **plan**, before code exists | Never |
| `05-domains/` | 2 | The **code**, once it does | Yes, where it applies |

`05-domains/` reviews code *against* the plan, so it structurally cannot see a defect *in*
the plan — it will happily confirm that a well-built thing was built well when the thing
should not have been built. If your question is answerable before any code is written, it
belongs in `03-planning/`.

Which rules load is decided by one table, `00-system/checklist-selection.json`, for both
folders. Do not add a second table to a folder manifest: two tables are two answers.

## Breadth - a new domain folder
A task needed a domain with no rules at all. Create `05-domains/<domain>/`, add a
`manifest.json`, and write the rules you actually needed. Do not speculate beyond them.

## Depth - a new rule in an existing folder
An edge case bit you inside a domain that already exists. Add one rule file. Update the
folder's `manifest.json` in the same edit - a manifest that lies is worse than no manifest.

## Research - a rule the repository has not learned yet
A task reached a domain where no checklist exists and no mistake has been made yet, so
neither breadth nor depth applies. Research the golden rule rather than inventing one.

**Never assume, never guess, never work from memory.** Every item cites an authoritative
source, recorded on the item itself: `source`, `source_version`, `source_authority` (the
1-10 scale in `docs/checklist-system.md` section 3), `source_consensus` (independent
sources at authority >= 7) and `source_established`. An item you cannot source does not
ship - the shortfall is the rule working, not an omission. `confidence_level` is then
**derived** by `hooks/workflow_hook.py::derive_confidence`; never type one by hand.

Cite the exact edition. `docs/checklist-system.md` section 4 records five version defects
found in this library's own source documents, including a citation ("ASVS 5.10") that was
malformed in a way `source_version` would have exposed on sight.

**Write it as questions, not prescriptions.** *"Does this class have one reason to
change?"* — not *"use an interface for every service"*. A question makes the reader look at
the code; a prescription tells them what to type and stops being right the moment the
codebase differs from the one it was written for. General enough to carry to another
project, specific enough that a violation is recognisable.

**Then run it against real work before keeping it** — real code for a `05-domains/` rule,
a real plan for an `03-planning/` one. A checklist that finds nothing in a thousand lines
is too vague to be worth loading, and you will not discover that by reading it. Record what
the trial found, including which questions did not apply.

Trial it against something you wrote, not something convenient. `03-planning/` was first
run against the plan that created it and returned ten findings on its own author — an
absent out-of-scope list, an unstated rollback, and an unnamed assumption among them. A
checklist that flatters the plan it shipped with has not been tested.

A researched rule is `convention` unless you can name the hook or test that enforces it,
and it is **proposed, not ratified** — surface it in the handover so a human decides
whether it stays. The self-hardening rule below still governs anything harvested from an
actual mistake.

## Blueprint refinement
A human corrected a component choice. Update the blueprint's mutable variables so the next
task starts from the corrected version. `06-components/BLUEPRINT_SCHEMA.md` defines the
shape, and the bar for writing one at all: a pattern earns a blueprint after it has shipped
and survived review, never in advance of that.

## The self-hardening rule
A mistake recorded **twice** in `docs/RETROSPECTIVE.md` stops being a note and becomes
structure: a checklist item in `.claude/skills/adaptive-workflow/SKILL.md` and a rule file under
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
