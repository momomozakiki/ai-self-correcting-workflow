# Golden rules

A golden rule is a checklist item proven enough to carry into **every** project. Not a
preference, not a style — something that exists because of a failure it prevents.

## Two layers, and the split is the whole design

| Layer | Lives in | Who writes it | Lifetime |
|---|---|---|---|
| **Golden base** | `golden-rules/<domain>/*.md` | Humans, or an orchestrator filling a gap | Permanent, carried to every project |
| **Project layer** | `plans/<project>/checklists/<domain>.md` | The agent working the project | That project only |

An agent **reads** the golden base and **appends** to the project layer. It never edits the
base mid-project. A project-layer item is promoted into the base only on evidence — see
`GROWTH.md`.

## File format

No frontmatter, no ids, no schema. One file, grouped by *when it applies*:

```markdown
# Git — golden rules (existing project)

Status: ratified 2026-08-29
Applies when the repo already has commits and a remote.

## Before touching anything
- [ ] `git fetch --all --prune`
- [ ] `git status --short` — if dirty, stop and ask; never stash silently

Sources: Pro Git, 2nd ed. (Chacon & Straub, 2014) ch.3.
```

## `Status:` — exactly two forms

- `Status: ratified YYYY-MM-DD` — a human has read it.
- `Status: drafted by orchestrator YYYY-MM-DD, unreviewed` — authored to fill a gap, not yet
  read by a human. An agent may use it, but must say so in its report.

**Any edit to a golden base resets the stamp to unreviewed.** Ratification is per-version, not
per-file. A stamp that outlives the content it described is the drift this repo has already
recorded happening inside a single commit.

## Where an item comes from

Every `##` group carries one `Sources:` line. Two legitimate kinds, and the difference is
worth stating in the line itself:

- **Authority** — a real, checkable document, **version-pinned**: `Pro Git, 2nd ed. (2014)`,
  not `Pro Git`. The old JSON library's required `source_version` field caught five genuine
  citation defects (a malformed ASVS level, a superseded IEEE 1012, RFC 7231 obsoleted by
  9110, two superseded ISO standards). Prose alone will not catch those, so the version is
  part of the citation, not decoration.
- **Incident** — a failure that actually happened here, dated and named:
  `Incident 2026-08-29 — branched from a base missing every file the plan targeted.`

An incident-sourced item is not weaker than an authority-sourced one. It is usually stronger:
it is the only kind of item guaranteed to have prevented something real.

Where neither exists, say so honestly — `Source: reasoned from first principles, YYYY-MM-DD`.
An honest gap flags the item for review. A fabricated citation does not.

## How much checklist does a one-line change pull in?

**The file is the loading unit, and that is coarser than what it replaces. Say so plainly: it
is a token-budget regression, not a detail.**

The JSON library selected *items* through one table (`checklist-selection.json`), keyed on task
size and context. Applying that table over the live rule files on 2026-08-30 gives the measured
figures:

| Phase 2, by task size | items | | Phase 2 at `new_module`, by context | items |
|---|---|---|---|---|
| `typo_fix` | 9 | | `deployment` | 13 |
| `small_change` | 50 | | `skill_work` | 17 |
| `new_module` | 88 | | `authentication` | 25 |
| `major_refactor` | 88 | | `database_work` | 26 |
| | | | `security_audit` | 33 |
| Phase 1, by task size | items | | `new_api` | 34 |
| `typo_fix` | 0 | | `code_review` | 38 |
| `small_change` | 26 | | | |
| `new_module` / `major_refactor` | 31 | | | |

So a typo fix cost **9 items** and a REST API **34**. Here, a typo fix in a git repository loads
`git/existing-project.md` — about 20 items — because there is no smaller unit than the file.
Below roughly `small_change`, this format loads **more**; at `new_module` and above it loads
**far less**, because nothing pulls in 88 items at once.

Two things keep that honest rather than merely cheaper:

- **The ~20-item ceiling is the budget.** It is enforced by `tests/test_golden_rules.py`, and
  the way to stay under it is to split a file by *when it applies* — `git/new-project.md` and
  `git/existing-project.md` are that split. Splitting is the selection mechanism.
- **Groups are the second dial.** A file is grouped by *when*, so a reader who does not touch
  shared state skips that group honestly rather than skimming everything.

What is genuinely lost is automatic, per-task selection: nothing computes which file to load
from a declared task size. Until an orchestrator does that (stage 5 of
`plans/golden-rules-migration.md`), choosing the file is a judgement the agent makes and states.

## How to write one

See `AUTHORING-GUIDE.md`. The short version: where there is one correct action, write the
**command**; where the answer depends on context, write a **question**. Getting that altitude
wrong is what makes a checklist feel useless.
