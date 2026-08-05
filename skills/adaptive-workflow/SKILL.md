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

## Tier 0 — absolute prohibitions

Not overrideable by config, by instruction, or by you:

- **Never force-push a shared or protected branch.** Propose a forward-fixing
  commit, or force-push only your own topic branch after confirming nobody pulled it.
- **Never commit secrets, credentials, tokens, or private keys.** If one is already
  committed, say so plainly and treat it as compromised — rotation is required;
  scrubbing history is not sufficient on its own.
- **Never rewrite published history.** No rebase/amend/reset on pushed commits.
- **Never delete or rewrite the ledger or the plan archive.** They are the audit
  trail. Correct an entry by appending, never by editing history away.

Full set with rationale: `.ai/02-market-rules/prohibitions/`.

**Three of these are enforced, not just written down.** A `PreToolUse` guard in
`hooks/workflow_hook.py` inspects every Bash and PowerShell command: it *denies* a
force-push whose destination resolves to a protected branch and any deletion aimed at
the ledger or plan archive, and *asks* before a history rewrite or a heredoc — cases
where the command alone cannot settle the question. Two things follow. Don't treat a
block as a bug to route around; it is the prohibition working. And don't treat the
absence of a block as permission: the guard fails open, sees tool calls only, and has
nothing at all to say about **secrets** — that one is still on you.

## Model choice (Claude Pro)

Sonnet 5 handles routine work; `/model opus` for hard passes — Opus has its own
weekly cap. **Fable 5 bills pay-as-you-go usage credits on Pro**, so never set it
as a default anywhere. See GUIDE §14.

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
  If a `SCOPE.md` exists in a directory you are about to work in, load it as
  supplementary **static** context (per-directory scope — see the Progressive
  Disclosure Guide §3.1). This is an optional scaling tier; most projects have none.
- **F4 Unfinished plan / roadmap.** If `plans/UNFINISHED.md` exists, surface it
  immediately and ask whether to continue or archive. Note the next unchecked
  item from the first active roadmap epic.
- **F5 Daily workflow update check** (once/day). If `.claude/workflow-core`
  submodule is absent, skip (and don't create the date file). Otherwise, if
  `.ai/.workflow_check_date` ≠ today: `git fetch` in the submodule, compare with
  `origin/main`; if behind, offer to update. Write today's date afterward.
  When `workflow_update_check.enabled` is set in `workflow_config.json`, the
  SessionStart hook performs this fetch/compare for you and injects a
  `🔄 Workflow updates available` notice — it never auto-applies; you still ask
  the user before running `git submodule update --remote`.

## Phase 1 — Meta-Planning

Assess the request: scope (fix/feature/refactor/architecture), documentation
impact, multi-session handoff (→ `UNFINISHED.md`), validation rigor, retro
value, **provenance** need (external docs?), and **ledger** steps.

Chunk large tasks against the roadmap; pick the next unblocked task as the
current `UNFINISHED.md` item. Produce a concrete bullet checklist with
acceptance criteria including only the necessary process steps. Optionally
confirm the plan with the user.

**Declare `task_size` here**, before the work exists — `typo_fix`,
`small_change`, `new_module` or `major_refactor`. It selects which review
checklists load, so it has to be decided while it can still shape the work. It
is a judgement, not a measurement: deriving it from `git diff --stat` would give
an empty diff at the moment you need the answer. **State it in the plan, with
your reason**, so the user can object while objecting still costs nothing —
not afterwards in the summary, when the run is already committed.

**Then review the plan against `.ai/03-planning/`.** Those five checklists ask
whether the problem is stated separately from the solution, whether each
acceptance criterion is verifiable and singular, what the rollback is, which
alternative was rejected and why, and how this will be proven — before any code
exists. A plan is the cheapest artifact to fix and the most expensive to get
wrong: everything downstream inherits its mistakes, and `.ai/05-domains/` cannot
catch them because it reviews code against the plan, not the plan itself.

**The selection rules live in `.ai/00-system/checklist-selection.json` — read
them there rather than from a copy.** One table covers both folders. A rule
loads when its `workflow_phase` matches the phase you are in, its
`task_size_required` includes your declared size, *and* its
`tech_stack_required` is either empty or intersects the project's stack. That
intersection keeps SQL rules out of a NoSQL project and keeps a typo fix from
pulling in eighty items. Phase-1 rules are never stack-gated — a plan's problem
statement is no better for being written in Go.

## Phase 2 — Execute

For each checklist item: **implement → run linter/formatter/tests → fix
failures before moving on.** If blocked, log the obstacle, propose an updated
plan, await approval, continue.

**Three execution guards:**

- **Reversibility.** Git is the rollback mechanism — make sure a clean commit
  checkpoint exists before anything hard to undo. If an operation can't be
  reversed, say so *before* running it.
- **Loops.** If a call repeats with identical arguments and no progress, change
  the approach — vary the arguments, read the error, or ask. The hook flags this
  at 3 consecutive identical calls, but noticing first is cheaper.
- **No heredoc stdin.** Never feed a program or a multi-line message to a command
  over a heredoc. Write the script to a file and run the file; use the editing
  tools for source changes. Escapes get mangled silently. For git: `git commit -m`
  (repeatable) or `-F <file>` — never `-F -`, a heredoc, or a bare `git commit`.
  The `PreToolUse` guard now *asks* on all four forms rather than blocking, because
  the occasional legitimate heredoc shouldn't become a wall. Answering the prompt
  isn't the fix — writing the file is.

**Conditional triggers (apply during and after each change):**

| Trigger | Action |
|---------|--------|
| New pattern / rule / gotcha | Append to `.ai/best_practices.md` (with example). |
| New naming convention | Append to `.ai/naming_conventions.md`. |
| Change to public API / architecture / data flow | Update `docs/*.md` (dated). |
| Doc created / updated | Apply the Documentation Standard: frontmatter (provenance + version) + `last_validated` refresh + a Revision History row; fold into a folder per §6.4 if it outgrows one question / its token budget, or its Revision History passes ~8 rows (relocate history to a sibling `CHANGELOG.md`). |
| Non-obvious technical decision | Decision log in `plans/archive/<slug>/execution_log.md`. |
| New significant directory with a distinct responsibility (large/monorepo projects) | Optionally add a `SCOPE.md` describing its role + DO/DON'T rules; link it from the parent's `SCOPE.md` (Progressive Disclosure Guide §3.1). Skip for small projects. |
| Repeatable mistake | Warning in best practices / retro note. |
| **Any intentional change** (not a trivial typo/whitespace edit) | **Append a ledger entry** to `history/YYYY-Www.md`. Add an optional `**Risk:**` line using one of `privilege \| design \| behavioral \| structural \| accountability` when the change carries real risk — omit it when it doesn't, or the field stops meaning anything. |
| Mistake worth remembering | Entry in `docs/RETROSPECTIVE.md`. If it's already there, append `(recurring)` to the heading — it now owes a rule file under `.ai/01-phases/` and a line here. |
| New rule harvested from a real mistake | Add the rule file, update the folder's `manifest.json` in the same edit, mirror it into `templates/ai-library/`, and set `enforcement_status` honestly: `live` needs an `enforced_by` list naming real code, `convention` needs an `enforcement_note` saying what the real mechanism is. `tests/test_governance_library.py` checks all of it. See `.ai/GROWTH.md`. |
| External doc without provenance | Ask for the official URL, then add the doc frontmatter (provenance fields). |
| Completed task affects roadmap | Update the roadmap. |
| Epic finished | Move it to `## Completed Epics`. |

**Ledger (mandatory).** Log every qualifying change in `history/YYYY-Www.md`
(create on first change of the week). Substantial → full `What / Why / Refs`;
trivial/routine → one-line note. Tags: `[design] [doc] [code] [workflow]
[config] [decision] [data]`. Reference commit SHA and/or plan slug.

**Documentation Standard (mandatory for every doc).** On creating or updating a
doc, add the YAML frontmatter block (provenance + version) and a Revision History
row; bump `version` on each non-trivial edit. Refresh `last_validated` **only when
you re-confirm the content is correct** (a content review) — a mechanical or
frontmatter-only edit leaves it unchanged, so it never overstates when the content was
last validated. For an external doc, ask "Is this from an official/authoritative
source? URL?" and set `official`/`source` accordingly. Agent-generated docs get
`official: false` + today's `last_validated` when the content is authored/reviewed now
(not for a frontmatter backfill on pre-existing content). If unconfirmed, mark
`official: unknown`.
Non-commentable formats (JSON, code) use a sidecar `.prov.md`. Split oversized docs
per the Progressive Disclosure Guide. Full spec: `GUIDE.md` §6.

## Phase 3 — Closure

- **Archive the plan:** move `UNFINISHED.md` → `plans/archive/YYYY-MM-DD_<slug>/plan.md`;
  create `execution_log.md` / `retro.md` only if the plan flagged them; delete
  `UNFINISHED.md` (it must not exist at rest).
- **Final ledger entry:** ensure all session changes are logged; append a
  closure summary.
- **Update roadmap** if triggered.
- **Retrospective:** log any mistake worth remembering; mark it `(recurring)` if
  it has happened before, and codify it (rule file + a line in this skill).
  `python hooks/workflow_hook.py --self-test` reports uncodified recurrences.
- **Commit & push:** `git add -A && git commit -m "Plan: <slug> – <summary>" && git push`.
  Multi‑paragraph message → repeated `-m` flags or `git commit -F <file>`. Avoid
  heredocs / `-F -` (the Bash safety layer can reject stdin‑fed commands) and a
  bare `git commit` (it can open an editor and hang).
- **Self-check:** not done until `UNFINISHED.md` is cleared, the ledger entry is
  written, and the commit is pushed.

---

## Documentation frontmatter

Markdown / HTML (place at the very top of the file):
```markdown
---
title: <Title>
version: 1.0                     # bump MINOR for content, MAJOR for restructure
last_validated: YYYY-MM-DD       # date you last re-confirmed the CONTENT is correct
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

**Folding into a folder (GUIDE.md §6.4):** a flat `docs/<name>.md` folds into
`docs/<name>/` when it breaks the "Rule of One Question" / exceeds its layer's token
budget (split per `docs/Progressive Disclosure Documentation Guide.md` — `index.md`
holds canonical frontmatter; children carry lightweight frontmatter + a link back),
**or** when its in-file Revision History passes ~8 rows. On folding, relocate the full
history to a sibling `CHANGELOG.md` (copy `templates/docs/CHANGELOG_TEMPLATE.md`);
keep only the latest ≤3 rows + a link in `index.md`. That `CHANGELOG.md` is a sibling
peer marked `exclude_from_ai: true`, so it stays out of the active token budget.

## Contributing improvements upstream

When you find a flaw or missing trigger in the workflow itself, classify it and
log the discovery in the project ledger with a `[workflow]` tag:

- **High** (a.k.a. **Critical** — breaks invariants / data loss / security): fix
  locally on `fix/<desc>` now, push, open a PR; may use the fix immediately.
- **Medium** (missing trigger, ambiguity, non-critical bug): open a
  `proposal/<desc>` PR with a plan; **do not** apply locally until merged.
- **Low / non-critical**: open an issue; optionally a draft branch, no PR.

"High" is the top tier; "Critical" is just another name for it, not a level above.
If you vendored the files (no submodule to push to), file a GitHub issue via the
**Workflow bug / flaw report** template instead of pushing a branch.

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
