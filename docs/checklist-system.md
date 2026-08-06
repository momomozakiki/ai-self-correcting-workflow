---
title: The checklist system — sourcing, confidence, and conditional loading
version: 1.2
last_validated: 2026-08-05
official: false
source: agent-generated
tags: [governance, checklists, sourcing, confidence, conditional-loading, plan-review]
applies_when: "Adding or revalidating a review checklist, or deciding which checklists a task should load."
estimated_tokens: 2200
---

# The checklist system
**Version 1.1** — *Consolidated from the Golden Rule Research & Checklist Creation
Protocol v2.0 and the Professional Hierarchical Checklist System v2.0, then extended to
review plans as well as code.*

## Revision History
| Version | Date | Change |
|---------|------|--------|
| 1.2 | 2026-08-06 | Adds `rule-skill-authoring-review` (8 items) to `05-domains/`, harvested from the skills-directory defect: eleven categories, 88 items for code review. Updates the skill paths to `.claude/skills/`. |
| 1.1 | 2026-08-05 | Adds §5a: plan review. `.ai/03-planning/` (5 rules, 31 items) reviews the plan at Phase 1; the selection table moves to `.ai/00-system/checklist-selection.json` and gains a `workflow_phase` axis. |
| 1.0 | 2026-08-05 | Consolidates the two staging documents. Records what was adopted, what was made workable, what was dropped, and the three citation defects found in the originals. |

---

## 1. What this replaces

Two documents previously sat in `docs/to-be-implement/`. Both are adopted here; both are
deleted. This file is the canonical record, and `.ai/05-domains/` is the working
instantiation. Where a mechanism could not work as literally specified, the workable
equivalent is built and the difference is stated — adopting a document means making it run,
not quoting it.

## 2. The governing principle: codify, don't constrain

Checklist items are **questions**, never prescriptions.

> *"Does this class have one reason to change?"* — not *"use an interface for every service."*

A question makes the reader look at the code and carries to a codebase it was not written
for. A prescription tells them what to type and stops being right the moment the context
differs. This is the one rule the whole folder rests on, and
`ChecklistItems.test_questions_are_questions` enforces the surface form of it.

## 3. Never assume — the sourcing rule

**No item ships without an authoritative source.** Not "common sense", not memory, not an
unverified blog. Every item carries `source`, `source_version`, `source_authority`,
`source_consensus` and `source_established`, and
`ChecklistItems.test_every_item_cites_a_source` fails the build if one does not.

### Source authority (1–10)

| Priority | Source type | Examples |
|---|---|---|
| 10 | Official standards | IETF RFCs, W3C, ISO, IEEE |
| 9 | Government / security frameworks | NIST, OWASP, SEI CERT, CISA |
| 8 | Official vendor documentation | Anthropic, Google, AWS, Microsoft |
| 7 | Peer-reviewed research | IEEE, ACM |
| 6 | Enterprise frameworks | CSA, published API guidelines |
| 5 | Industry authority books | *Clean Code*, *The Pragmatic Programmer* |
| 4 | Industry publications | trade press |
| 3 | High-voted, recent Q&A | — |
| 2 | General blogs | — |
| 1 | Unverified | forums, anonymous posts |

`source_consensus` is the **count of independent sources at authority ≥ 7** supporting the
same item. The tests enforce that it is present and numeric; **its accuracy is a human
gate**, surfaced in `plans/HANDOVER.md`. Saying so is the point — a number that looks
tested but is not is exactly what this system exists to prevent.

### Confidence is derived, never asserted

`confidence_level` (1–5) is computed by `.claude/hooks/workflow_hook.py::derive_confidence` from
authority, consensus and age. `CONFIDENCE_MATRIX` is an **ordered threshold ladder**, not a
lookup: the source table reads *"authority ≥ 10 **and** consensus ≥ 3 **and** age > 5
years"*, so `(10, 4, 6)` is also level 5.

| Level | Label | Requires |
|---|---|---|
| 5 | Industry Standard | authority ≥ 10, consensus ≥ 3, > 5 years |
| 4 | Enterprise-Proven | authority ≥ 8, consensus ≥ 2, > 3 years |
| 3 | Community-Validated | authority ≥ 6, consensus ≥ 1, > 1 year |
| 2 | Emerging | authority ≥ 4, consensus ≥ 1 |
| 1 | Uncertain | anything else |

`ChecklistItems.test_confidence_level_recomputes_from_the_items_own_fields` recomputes
every stored value and fails on disagreement — the same discipline `enforcement_mode`
follows, for the same reason: a number nobody can recompute drifts.

**The percentage ranges from the source documents are deliberately not modelled.** No
procedure distinguishes 94% from 96%. The level survives; the false precision does not.

### Revalidation

`--self-test` warns when an item's `last_validated` exceeds
`revalidation_interval_days` (default 180). Uniform, offline, needs no maintenance to stay
honest. **Not** source-version-change detection: that needs a hand-maintained version file
for arbitrary standards, which goes stale silently while nothing notices — the failure
already recorded in `RETROSPECTIVE.md`. Because each item stores `source_version`, clearing
a warning is one lookup.

## 4. The three citation defects found in the source documents

Validation was run on the documents *before* adopting them, since propagating a bad
citation would break the rule they exist to enforce. All three are corrected here.

| Claim in the originals | Verified against | Finding |
|---|---|---|
| *"OWASP ASVS 5.10"* for parameterized queries | ASVS 5.0.0, released 2025-05-30 | **Malformed.** ASVS numbers requirements `chapter.section.requirement`; "5.10" is two levels of a three-level scheme. The real requirement is **V1.2.4**, in chapter V1 *Encoding and Sanitization*. |
| *"NIST SP 800-190 requires non-root, read-only filesystems"* | NIST SP 800-190 | **Overstated.** Its read-only-filesystem guidance concerns container-specific *host* operating systems. It is a guide, not a conformance standard, and does not "require". Items citing it are phrased as questions about posture, not as mandates. |
| OWASP Top 10 **2021** as the security baseline | owasp.org | **Superseded in progress.** A Top 10 **2025 release candidate** exists. Items still cite stable 2021 — a release candidate is not authoritative — and carry a `revalidation_note` naming the pending edition. |

Two further version traps were caught while sourcing: **RFC 9110** obsoletes RFC 7231 (so
citing 7231 for HTTP semantics cites a superseded document), and **ISO/IEC 25010:2023**
revises the 2011 edition, replacing *usability* with *interaction capability* and
*portability* with *flexibility*.

That a validation protocol found five defects in its own companion documents is the
strongest available argument for adopting it.

## 5. Conditional loading

Loading all fifteen checklists for a typo fix wastes the context budget GUIDE §6.4 exists
to protect; loading none for a new API misses the point. **The selection rules live once,
as data, in `.ai/00-system/checklist-selection.json`.** Both `.claude/skills/adaptive-workflow`
and `.claude/skills/autonomous-task` read them there; neither restates the logic, because a copy is a
second thing to keep right.

A rule loads when its `workflow_phase` matches the phase in progress, its
`task_size_required` includes the declared task size, **and** its `tech_stack_required` is
empty or intersects the project's stack.

> **The table moved in v1.1.** It lived in `.ai/05-domains/manifest.json` under `selection`
> until plan-review rules arrived and would have needed a second copy. A domain manifest
> cannot be the authority on a folder it does not contain, and two tables are two answers.
> **Adopters who vendored the library before 2026-08-05 will find `selection` gone from the
> domain manifest** — it is at the new path, unchanged apart from the added `phases` block.
> `ChecklistSelection.test_no_folder_manifest_defines_its_own_selection` now fails the build
> if a folder grows its own table again.

**`task_size` is declared at Phase 1, before the work exists.** It is deliberately not
derived from `git diff --stat`: at planning time the diff is empty, and deriving it
afterwards would load the checklists after the code they were meant to guide. Being a
judgement, it is **stated in the plan with its reason**, so the user can object while
objecting still costs nothing — and repeated in the handover.

Measured on the current library:

| Task | Items loaded |
|---|---|
| Typo fix, Python | 9 (code quality only) |
| Small change, Python | 35 |
| New REST API, Postgres | 34 (api, error handling, performance, security) |
| New module, no database in the stack | 57 — and **no** database rule |
| Deploy change, Docker | 13 (devops, audit) |

**Known limit:** tech-stack gating is per *rule*, not per *item*. The database checklist
covers both SQL and NoSQL concerns, so a Mongo project loads it whole rather than only its
NoSQL items. The meaningful case — a project with no database at all — correctly loads
nothing.

## 5a. Plan review — the phase the checklists were missing

Every rule in `.ai/05-domains/` says the same thing in its `ai_action`: *work through the
checklist against the code in question*. That is eleven categories and 88 items, all of
which need work to exist before they can be answered. `rule-task-checklist` told the agent
to produce a plan checklist and supplied nothing to interrogate it with.

**So a plan was reviewed by nothing.** Not lightly — structurally. `05-domains/` reviews
code *against* the plan, which means it will confirm that a well-built thing was built
well when the thing should not have been built at all. No amount of code review reaches a
defect one level up.

`.ai/03-planning/` closes that: **5 rules, 31 items**, answered at Phase 1 before any code
exists.

| Rule | Items | Asks |
|---|---|---|
| `rule-problem-definition-review` | 6 | Is the problem stated separately from the solution? Is there evidence it is real? What does doing nothing cost? What will this deliberately not do? |
| `rule-requirements-review` | 7 | The ISO/IEC/IEEE 29148 characteristics, asked of acceptance criteria: verifiable, singular, unambiguous, necessary, feasible, appropriate, traceable |
| `rule-risk-and-reversibility-review` | 7 | What is the rollback, and has it been run? What is the blast radius? Can this ship as a smaller reversible increment? What was knowingly accepted? |
| `rule-alternatives-and-rationale-review` | 5 | Which alternative was rejected, and why? Was "do nothing" considered? Which assumption, if wrong, invalidates this? |
| `rule-verification-planning-review` | 6 | Is the check designed before the work? Can it fail? Does anything but the author's assertion confirm completion? |

**Never gated on tech stack.** A plan's problem statement is no better or worse for being
written in Go, so a stack filter at Phase 1 could only ever exclude a question that still
applied — silently. `ChecklistSelection.test_planning_rules_are_never_gated_on_tech_stack`
enforces it.

### Sources

Every item resolved against a current edition on 2026-08-05. Two were stale in the
process — the same defect class §4 records:

| Source | Authority | Note |
|---|---|---|
| ISO/IEC/IEEE 29148:2018 | 10 | Supersedes :2011. Nine characteristics of a well-formed requirement |
| ISO/IEC/IEEE 42010:2022 | 10 | 2nd ed. Adds Stakeholder Perspectives and Architecture Rationale |
| **IEEE 1012-2024** | 10 | **1012-2016 is superseded** — board-approved 2024-11-12, published 2025-08-22 |
| ISO 31000:2018 | 10 | Confirmed 2023. **Guidelines, not certifiable** — items say "does the plan identify", never "ISO 31000 requires" |
| INCOSE SE Handbook 5th ed. | 8 | June 2023, aligned to ISO/IEC/IEEE 15288:2023 |
| NASA/SP-2016-6105 Rev 2 | 8 | Rev 2, updated 2020-01-27 |
| Google SRE Book | 8 | Rollback and postmortem discipline |
| Threat Modeling Manifesto | 7 | 2020. "What can go wrong" as a planning question |
| Nygard, *Documenting Architecture Decisions* | 5 | The ADR form |

### The trial — run against its own plan

`.ai/GROWTH.md` requires a new checklist be run against real work before it is kept. These
were run against the plan that produced them (`major_refactor`, so all five loaded).
**Ten of thirty-one items found something**, including on the plan's author:

| Item | Finding |
|---|---|
| `PRB-DEF-05` | No out-of-scope list was written at all |
| `PRB-DEF-03` | Who benefits, and how they would notice, never stated |
| `REQ-CHR-07` | Moving the selection table is not traceable to the stated problem — it is a consequence the author introduced |
| `RSK-REV-01` | No rollback stated for the selection-table move |
| `RSK-REV-02` | Blast radius unstated: it is a **breaking change for adopters** who read `selection` from the domain manifest |
| `RSK-REV-03` | `03-planning/` could have shipped without moving the table — a smaller reversible increment existed and was not taken |
| `ALT-RAT-03` | "Do nothing" was never considered as an option |
| `ALT-RAT-05` | The load-bearing assumption was never named: **that a plan reviewed by the same agent that wrote it is worth anything.** Self-review has no independent signal |
| `VER-PLN-03` | Verification covers the checklists' *structure*; their *content quality* is untested |
| `VER-PLN-04` | Nothing checks that a plan actually gets reviewed — the failure this folder exists to prevent is itself unverified |

`RSK-REV-02` produced the adopter migration note in §5. `ALT-RAT-05` is recorded and not
solved: it is the honest limit of Phase-1 self-review, and the only real mitigation is the
user reading the answers.

A checklist that returned nothing here would have been too vague to keep.

## 6. What was adopted, changed, and dropped

| Component | Outcome |
|---|---|
| Questions over prescriptions | Adopted verbatim; tested |
| Source authority scale, mandatory citation | Adopted; tested |
| Confidence levels 1–5 | Adopted as a **derived** value; tested |
| Confidence *percentages* | **Dropped** — unmeasurable |
| Ten-category taxonomy | Adopted; all ten built. An eleventh, `skill-authoring`, was later harvested from a real defect rather than imported — which is the growth path `GROWTH.md` describes |
| Per-item IDs, remediation hints | Adopted; tested |
| Conditional loading | Adopted as manifest data |
| Revalidation triggers | **Changed** to timer-based; version detection needs a manifest that itself goes stale |
| Performance tracking | **Changed**: metrics append to `.ai/08-behavioral-metrics/`, never into rule files — mutable rule files would break `TemplateParity` on every run |
| Confidence self-adjustment (±2) | **Dropped.** The agent that applied a rule would also decide its own false-positive rate, then feed that grade back into whether the rule is trusted. No ground truth anywhere in the loop. Drift is reported for human ratification instead |
| `next_validation` date | **Dropped** — nothing scheduled it |
| ~200 items | **88 delivered** for code review, **31 more** for plan review. Every one sourced; the shortfall is the sourcing rule working, not an omission |
| Code review as the only review | **Extended.** Both source documents assumed a checklist reviews code. `03-planning/` reviews the plan — see §5a |

## 7. Adding a checklist

See `.ai/GROWTH.md` for the growth protocols. In short: pick the folder by asking whether
the question is answerable before code exists (`03-planning/`) or only after
(`05-domains/`), research it, phrase it as questions, cite every item against a current
edition, **run it against real work before keeping it** — a checklist that finds nothing is
too vague to be worth loading, and reading it will not tell you that — then surface it in
the handover as *proposed*, not ratified.

Do not add a selection table to a folder manifest. There is one, at
`.ai/00-system/checklist-selection.json`, and a test enforces that there stays one.
