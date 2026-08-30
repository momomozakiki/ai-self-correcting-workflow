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
`.claude/hooks/workflow_hook.py` inspects every Bash and PowerShell command: it *denies* a
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

**Declare what you owe, in the plan, on one line.** `Checklists: <paths>`, naming the
`golden-rules/` files this task will be reviewed against — or `Checklists: none — <reason>`
when none applies, which below roughly `small_change` is the expected answer rather than an
evasion. Declaring is a decision made while objecting is still cheap; an absent line is an
omission nobody can see. `tests/test_checklist_reports.py` requires the line.

**Then generate the report skeletons, before doing the work**, one per declared file at
`plans/<plan>/checklists/<same path>`, every verdict `todo`:

```
python -c "import sys; sys.path.insert(0,'scripts'); import checklist_report as cr; ..."
```

or by hand from `golden-rules/REPORTING.md`. Writing them first is not bookkeeping: a checklist
loaded at Phase 1 can fall out of context before Phase 2 ends, and a session that dies leaves
its outstanding items named on disk.

## Phase 2 — Execute

For each checklist item: **implement → run linter/formatter/tests → fix
failures before moving on.** If blocked, log the obstacle, propose an updated
plan, await approval, continue.

**Work the report as your to-do list.** Replace each `todo` with `pass`, `finding`,
`cannot tell from here`, or `n/a` as you answer it — the last three carry a reason. Report the
answers *including the ones that pass*; a checklist that only ever surfaces problems reads as
noise. Where a plan simply does not address an item, that absence **is** the answer: do not
fill it in from what you intended.

You may add to `## Working notes` freely — decomposition, steps you discover. You may **not**
add or remove lines in the verdict block: an agent that can add items to the thing deciding
whether it is finished can always reach "finished". A discovered step that recurs gets promoted
into the golden file itself, per `GROWTH.md`. At Phase 3, `python scripts/checklist_status.py`
must report CLOSED.

**Four execution guards:**

- **Settle disputes by direct test.** When a claim about how the system behaves is
  disputed or uncertain, *run it* — don't argue it. Use the docs to design the test,
  never in place of one, and test **every** competing claim, including your own.
  Report the raw output, not a paraphrase. If it genuinely can't be executed, label it
  unproven and say what would settle it; the best-argued position is not a result.
  When the user has to run it, write the instructions in plain language — what to do,
  what a pass looks like, what a failure looks like, and why you can't do it yourself.
  Assume no expertise: no jargon, no "simply run", no assuming they know what a hook is.
  Nothing enforces this — see `.ai/01-phases/rule-direct-test-disputes.json`.
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

**Then apply the conditional triggers** — the "if you did X, record Y" table,
including the mandatory ledger entry:
[references/conditional-triggers.md](references/conditional-triggers.md).

**Every doc you create or update** takes the frontmatter, provenance and folding
rules in [references/doc-frontmatter.md](references/doc-frontmatter.md).

## Phase 3 — Closure

- **Archive the plan:** move `UNFINISHED.md` → `plans/archive/YYYY-MM-DD_<slug>/plan.md`;
  create `execution_log.md` / `retro.md` only if the plan flagged them; delete
  `UNFINISHED.md` (it must not exist at rest).
- **Final ledger entry:** ensure all session changes are logged; append a
  closure summary.
- **Update roadmap** if triggered.
- **Retrospective:** log any mistake worth remembering; mark it `(recurring)` if
  it has happened before, and codify it (rule file + a line in this skill).
  `python .claude/hooks/workflow_hook.py --self-test` reports uncodified recurrences.
- **Commit & push:** clear the breadcrumb *first*, then
  `git add -A && git commit -m "Plan: <slug> – <summary>" && git push`.
  Multi‑paragraph message → repeated `-m` flags or `git commit -F <file>`. Avoid
  heredocs / `-F -` (the Bash safety layer can reject stdin‑fed commands) and a
  bare `git commit` (it can open an editor and hang).
  **`git add -A` sweeps in `plans/UNFINISHED.md` (recurring).** The Stop hook rewrites
  that breadcrumb on every dirty-tree turn, so it is almost always present when you
  commit mid-task. It is transient session state, not an artifact, and it has been
  committed by accident twice (`ceb17c2` → fixed by `3feacb3`; recurred 2026-08-06).
  The path is deliberately **not** gitignored, because a human-authored plan lives at
  the same path and ignoring it would make that plan uncommittable. So the check is
  manual: before every `git add -A`, confirm the file is either absent or a real plan —
  `head -1 plans/UNFINISHED.md` showing `<!-- workflow-hook: auto-breadcrumb -->` means
  do not commit it. Recover with `git rm --cached plans/UNFINISHED.md`.
- **Self-check:** not done until `UNFINISHED.md` is cleared, the ledger entry is
  written, and the commit is pushed.

---

## Reference files

- [references/conditional-triggers.md](references/conditional-triggers.md) — the
  Phase 2 trigger table and the ledger format.
- [references/doc-frontmatter.md](references/doc-frontmatter.md) — the
  Documentation Standard: frontmatter, sidecars, folding.
- [references/contributing-upstream.md](references/contributing-upstream.md) —
  classifying and contributing a fix to the workflow itself.

Writing or restructuring a skill is its own job — see the
[skill-authoring](../skill-authoring/SKILL.md) skill.

---

## Quick reference

- **Phase 0:** git sync · env check · load docs (+provenance) · unfinished plan
  & roadmap · daily update check.
- **Phase 1:** assess scope/docs/provenance/ledger · declare `task_size` · chunk
  via roadmap · write checklist · review it against `.ai/03-planning/`.
- **Phase 2:** implement → lint/test → apply triggers (ledger, docs, provenance,
  roadmap) → log obstacles.
- **Phase 3:** archive plan · final ledger entry · roadmap · retrospective ·
  commit & push · confirm the three closure conditions.
