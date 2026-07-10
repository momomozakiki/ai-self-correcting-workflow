---
name: adaptive-workflow
description: Agent operating manual for the Adaptive Self-Correcting Workflow. Invoke at the start of any coding session in a project that has adopted workflow-core, and whenever making intentional changes (code, docs, config, design) that must be logged, verified for provenance, or handed off across sessions. Covers the Phase 0-3 checklists, the weekly change-history ledger, source provenance, and the upstream contribution process.
---

# Adaptive Self-Correcting Workflow — Agent Manual

You are operating in a project that adopts **workflow-core**. Follow these
phases. Hooks give ambient reminders; this skill is the authoritative process.
Full reference: `.claude/workflow-core/GUIDE.md`.

Configuration lives in `.claude/workflow_config.json` (paths + feature flags).
Read it to resolve generic concepts (source dirs, ledger dir, roadmap file) to
this project's actual paths.

---

## Phase 0 — Fixed Invariants (always, first)

- **F1 Git sync.** `git fetch && git pull --rebase`. If the working tree is
  dirty, **stop and ask** the user how to handle it (continue / stash / commit).
- **F2 Environment.** For each tool in `env_check.tool_paths`: run
  `<path> <version_flag>` for a version, or — if `version_flag` is `null`/empty —
  only verify the path exists. Report versions or found/not-found. Empty config → skip.
- **F3 Living docs.** Load the configured docs. For each, check for the doc
  frontmatter (provenance + version fields, or sidecar `.prov.md`). If missing,
  **flag but do not block**: "Document [file] has no frontmatter — is it official?"
- **F4 Unfinished plan / roadmap.** If `plans/UNFINISHED.md` exists, surface it
  immediately and ask whether to continue or archive. Note the next unchecked
  item from the first active roadmap epic.
- **F5 Daily workflow update check** (once/day). If `.claude/workflow-core`
  submodule is absent, skip (and don't create the date file). Otherwise, if
  `.ai/.workflow_check_date` ≠ today: `git fetch` in the submodule, compare with
  `origin/main`; if behind, offer to update. Write today's date afterward.

## Phase 1 — Meta-Planning

Assess the request: scope (fix/feature/refactor/architecture), documentation
impact, multi-session handoff (→ `UNFINISHED.md`), validation rigor, retro
value, **provenance** need (external docs?), and **ledger** steps.

Chunk large tasks against the roadmap; pick the next unblocked task as the
current `UNFINISHED.md` item. Produce a concrete bullet checklist with
acceptance criteria including only the necessary process steps. Optionally
confirm the plan with the user.

## Phase 2 — Execute

For each checklist item: **implement → run linter/formatter/tests → fix
failures before moving on.** If blocked, log the obstacle, propose an updated
plan, await approval, continue.

**Conditional triggers (apply during and after each change):**

| Trigger | Action |
|---------|--------|
| New pattern / rule / gotcha | Append to `.ai/best_practices.md` (with example). |
| New naming convention | Append to `.ai/naming_conventions.md`. |
| Change to public API / architecture / data flow | Update `docs/*.md` (dated). |
| Doc created / updated | Apply the Documentation Standard: frontmatter (provenance + version) + `last_validated` refresh + a Revision History row; split per the Progressive Disclosure Guide if oversized. |
| Non-obvious technical decision | Decision log in `plans/archive/<slug>/execution_log.md`. |
| Repeatable mistake | Warning in best practices / retro note. |
| **Any intentional change** (not a trivial typo/whitespace edit) | **Append a ledger entry** to `history/YYYY-Www.md`. |
| External doc without provenance | Ask for the official URL, then add the doc frontmatter (provenance fields). |
| Completed task affects roadmap | Update the roadmap. |
| Epic finished | Move it to `## Completed Epics`. |

**Ledger (mandatory).** Log every qualifying change in `history/YYYY-Www.md`
(create on first change of the week). Substantial → full `What / Why / Refs`;
trivial/routine → one-line note. Tags: `[design] [doc] [code] [workflow]
[config] [decision] [data]`. Reference commit SHA and/or plan slug.

**Documentation Standard (mandatory for every doc).** On creating or updating a
doc, add the YAML frontmatter block (provenance + version) and a Revision History
row; bump `version` and refresh `last_validated` on each non-trivial edit. For an
external doc, ask "Is this from an official/authoritative source? URL?" and set
`official`/`source` accordingly. Agent-generated docs get `official: false` +
today's `last_validated` automatically. If unconfirmed, mark `official: unknown`.
Non-commentable formats (JSON, code) use a sidecar `.prov.md`. Split oversized docs
per the Progressive Disclosure Guide. Full spec: `GUIDE.md` §6.

## Phase 3 — Closure

- **Archive the plan:** move `UNFINISHED.md` → `plans/archive/YYYY-MM-DD_<slug>/plan.md`;
  create `execution_log.md` / `retro.md` only if the plan flagged them; delete
  `UNFINISHED.md` (it must not exist at rest).
- **Final ledger entry:** ensure all session changes are logged; append a
  closure summary.
- **Update roadmap** if triggered.
- **Commit & push:** `git add -A && git commit -m "Plan: <slug> – <summary>" && git push`.
- **Self-check:** not done until `UNFINISHED.md` is cleared, the ledger entry is
  written, and the commit is pushed.

---

## Documentation frontmatter

Markdown / HTML (place at the very top of the file):
```markdown
---
title: <Title>
version: 1.0                     # bump MINOR for content, MAJOR for restructure
last_validated: YYYY-MM-DD       # refresh on every non-trivial edit
official: false                  # true | false | unknown
source: agent-generated          # URL | agent-generated | user-provided, origin unknown
tags: [<retrieval tags>]
applies_when: "<when this doc is relevant>"
estimated_tokens: <int>
---

# <Title>
**Version 1.0** — *<one-line scope>*

## Revision History
| Version | Date       | Change   |
|---------|------------|----------|
| 1.0     | YYYY-MM-DD | Initial. |
```

Sidecar (for JSON/code) — `config.json` → `config.json.prov.md`:
```markdown
# Provenance for config.json
- version: 1.0
- last_validated: YYYY-MM-DD
- official: false
- source: agent-generated
- notes: ...
```

**Splitting:** when a doc breaks the "Rule of One Question" or exceeds its layer's
token budget, split per `docs/Progressive Disclosure Documentation Guide.md`
(index holds canonical frontmatter; children carry lightweight frontmatter + a link back).

## Contributing improvements upstream

When you find a flaw or missing trigger in the workflow itself, classify it and
log the discovery in the project ledger with a `[workflow]` tag:

- **High** (breaks invariants / data loss / security): fix locally on
  `fix/<desc>` now, push, open a PR; may use the fix immediately.
- **Medium** (missing trigger, ambiguity, non-critical bug): open a
  `proposal/<desc>` PR with a plan; **do not** apply locally until merged.
- **Low / non-critical**: open an issue; optionally a draft branch, no PR.

See `.claude/workflow-core/CONTRIBUTING.md` for the full process.

---

## Quick reference

- **Phase 0:** git sync · env check · load docs (+provenance) · unfinished plan
  & roadmap · daily update check.
- **Phase 1:** assess scope/docs/provenance/ledger · chunk via roadmap · write
  checklist.
- **Phase 2:** implement → lint/test → apply triggers (ledger, docs, provenance,
  roadmap) → log obstacles.
- **Phase 3:** archive plan · final ledger entry · roadmap · commit & push ·
  confirm the three closure conditions.
