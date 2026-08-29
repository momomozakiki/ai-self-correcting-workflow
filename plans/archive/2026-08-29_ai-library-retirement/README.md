# `.ai/` library — archived 2026-08-29

Verbatim copy of the governance library at the point it began to be retired, taken **before**
any deletion. Two trees, 58 files each:

- `ai-library/` — the live library (`.ai/`)
- `templates-ai-library/` — the adopter copy (`templates/ai-library/`)

## Why this exists

Not sentiment. This is the **raw material** for the golden-rules domains that replace it.
`golden-rules/` is seeded empty on purpose — a rule nobody hit yet is a guess — but when a
project first needs a `security`, `database`, `api`, `performance`, `testing`,
`error-handling`, `architecture`, `code-quality`, `devops`, `audit` or `skill-authoring`
domain, the sourced checklist for it already exists here and should be the starting point
rather than a blank page.

Eleven domain checklists in `ai-library/05-domains/`, five plan-review categories (31 items)
in `03-planning/`, thirteen phase rules in `01-phases/`, four prohibitions in
`02-market-rules/prohibitions/`.

## What was worth keeping, and why

The retirement drops the **distribution and metadata** machinery — per-item
`confidence_level` derivation, `source_consensus`, the CISA `risk_source`/`risk_weight` bands,
`manifest.json` bookkeeping with `total_items`, the maturity ladder, and the
`templates/ai-library/` mirror. That is bookkeeping about rules, not rules.

It keeps the **content**: the questions themselves, and their citations. Two things in
particular are ported forward rather than archived, because they have no equivalent in a
domain taxonomy:

- `03-planning/` — the only artifact here that reviews a **plan** rather than code. A domain
  checklist reviews code *against* the plan and so cannot see a defect *in* the plan.
- `01-phases/` — thirteen rules codifying mistakes that recurred twice. These are phases, not
  domains; "a future project will re-author them" does not apply.

## The one field worth carrying over

`source_version`. It was a required field, and filling it in caught five genuine citation
defects: a malformed ASVS level (two levels of a three-level scheme), a superseded
IEEE 1012-2016, RFC 7231 obsoleted by 9110, and two superseded ISO standards. The golden-rules
format keeps version pinning in its `Sources:` line for exactly this reason.

## Do not edit

This is a record of a prior state. Corrections go to the live `golden-rules/` tree, not here.
