---
title: The checklist system — sourcing, confidence, and conditional loading
version: 1.0
last_validated: 2026-08-05
official: false
source: agent-generated
tags: [governance, checklists, sourcing, confidence, conditional-loading]
applies_when: "Adding or revalidating a review checklist, or deciding which checklists a task should load."
estimated_tokens: 1800
---

# The checklist system
**Version 1.0** — *Consolidated from the Golden Rule Research & Checklist Creation
Protocol v2.0 and the Professional Hierarchical Checklist System v2.0.*

## Revision History
| Version | Date | Change |
|---------|------|--------|
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

`confidence_level` (1–5) is computed by `hooks/workflow_hook.py::derive_confidence` from
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

Loading all ten checklists for a typo fix wastes the context budget GUIDE §6.4 exists to
protect; loading none for a new API misses the point. **The selection rules live once, as
data, in `.ai/05-domains/manifest.json` under `selection`.** Both
`skills/adaptive-workflow` and `skills/autonomous-task` read them there; neither restates
the logic, because a copy is a second thing to keep right.

A rule loads when its `task_size_required` includes the declared task size **and** its
`tech_stack_required` is empty or intersects the project's stack.

**`task_size` is declared at Phase 1, before the work exists.** It is deliberately not
derived from `git diff --stat`: at planning time the diff is empty, and deriving it
afterwards would load the checklists after the code they were meant to guide. Being a
judgement, it goes in the handover for a human to confirm.

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

## 6. What was adopted, changed, and dropped

| Component | Outcome |
|---|---|
| Questions over prescriptions | Adopted verbatim; tested |
| Source authority scale, mandatory citation | Adopted; tested |
| Confidence levels 1–5 | Adopted as a **derived** value; tested |
| Confidence *percentages* | **Dropped** — unmeasurable |
| Ten-category taxonomy | Adopted; all ten built |
| Per-item IDs, remediation hints | Adopted; tested |
| Conditional loading | Adopted as manifest data |
| Revalidation triggers | **Changed** to timer-based; version detection needs a manifest that itself goes stale |
| Performance tracking | **Changed**: metrics append to `.ai/08-behavioral-metrics/`, never into rule files — mutable rule files would break `TemplateParity` on every run |
| Confidence self-adjustment (±2) | **Dropped.** The agent that applied a rule would also decide its own false-positive rate, then feed that grade back into whether the rule is trusted. No ground truth anywhere in the loop. Drift is reported for human ratification instead |
| `next_validation` date | **Dropped** — nothing scheduled it |
| ~200 items | **80 delivered.** Every one sourced; the shortfall is the sourcing rule working, not an omission |

## 7. Adding a checklist

See `.ai/GROWTH.md` for the four growth protocols. In short: research it, phrase it as
questions, cite every item, **run it against real code before keeping it** — a checklist
that finds nothing in a thousand lines is too vague to be worth loading, and reading it
will not tell you that — then surface it in the handover as *proposed*, not ratified.
