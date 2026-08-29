# CLAUDE.md

> **This repository _is_ `workflow-core`.** It defines the Adaptive
> Self-Correcting Workflow and dogfoods it: the hooks in `.claude/settings.json`
> point at this repo's own `.claude/hooks/workflow_hook.py` (there is no
> `.claude/workflow-core` submodule here — this is the source). We practice what
> we preach, keeping our own ledger under `history/`.

<!-- ==================================================================== -->
<!-- BEGIN adaptive-workflow fragment (managed by .claude/workflow-core)   -->
<!-- Included verbatim; project-specific notes go OUTSIDE this block.      -->
<!-- ==================================================================== -->

## Adaptive Self-Correcting Workflow

This project follows the Adaptive Self-Correcting Workflow. The full reference
lives in `GUIDE.md`; the agent operating manual is the `adaptive-workflow` skill
(`.claude/skills/adaptive-workflow/SKILL.md`). Hooks provide ambient reminders —
treat them as helpful nudges, not blockers.

### Tier 0 — absolute prohibitions (never overrideable)
- Never force-push a shared branch. Never commit secrets. Never rewrite published
  history. Never delete the ledger or the plan archive.
- Full set: `.ai/02-market-rules/prohibitions/`.
- **Three of these are enforced.** A `PreToolUse` guard (`.claude/hooks/workflow_hook.py`,
  matcher `Bash|PowerShell`) *denies* a force-push resolving to a protected branch and
  any deletion aimed at `history/` or `plans/archive/`, and *asks* before a history
  rewrite or a heredoc. A block is the prohibition working, not an obstacle to route
  around. Equally: no block is not permission — the guard fails open, sees tool calls
  only, and does not check for **secrets** at all. GUIDE §7.5 has the limits.

### Fixed invariants — always do first (Phase 0)
- **F1 Git sync:** `git fetch && git pull --rebase`. If the tree is dirty, ask
  the user how to proceed before changing anything.
- **F2 Environment:** verify the tools in `workflow_config.json → env_check`.
- **F3 Living docs:** load configured docs; flag any missing doc frontmatter
  (provenance + version).
- **F4 Unfinished plan / roadmap:** if `plans/UNFINISHED.md` exists, surface it
  immediately; note the next unchecked roadmap item.
- **F5 Daily workflow update check:** once per day (N/A here — this is the source).

### Per-task discipline
- **Plan (Phase 1):** design a task-specific checklist covering tests, doc
  updates, ledger entries, provenance, and roadmap impact.
- **Execute (Phase 2):** implement → run linter/tests → apply conditional
  triggers. **Log every intentional change** to the weekly ledger
  `history/YYYY-Www.md` (skip only trivial typo/whitespace-only edits). Add doc
  frontmatter (provenance + version) to any new or updated document.
- **Close (Phase 3):** archive the plan, write the final ledger entry, update
  the roadmap, then commit & push. You are **not done** until `UNFINISHED.md`
  is cleared, the ledger entry is written, and the commit is pushed.

<!-- END adaptive-workflow fragment -->

## Settle disputes by direct test

When a claim about how the system behaves is disputed or uncertain, **run it — don't argue
it.** Use the docs to design the test, never in place of one, and test *every* competing claim,
including your own. Report the raw output. If it genuinely cannot be executed, label it
unproven and say what would settle it; the best-argued position is not a result.

When the user has to run it, write the instructions in plain language: what to do, what a pass
looks like, what a failure looks like, and why you cannot do it yourself. Assume no expertise.

Ungated here on purpose — a `paths:`-scoped rule is not re-injected after `/compact`.
Rule: `.ai/01-phases/rule-direct-test-disputes.json`.

## Project-specific notes

Split into `.claude/rules/`, which load alongside this file:

- **[repo-conventions.md](.claude/rules/repo-conventions.md)** — stdlib-only constraint, the
  four documents that drift together, the health check, autonomous runs, runtime and model
  choice, commit hygiene, no heredoc stdin.
- **[governance-library.md](.claude/rules/governance-library.md)** — `.ai/` enforcement tiers.
  The `templates/ai-library/` mirror requirement is **gone** (2026-08-29); the file says so.
- **[claude-code-layout.md](.claude/rules/claude-code-layout.md)** — path-scoped to
  `.claude/**`; discovered-vs-registered, the mirrors, frontmatter near-misses.

**Skills live in `.claude/skills/`** because that is one of the only places Claude Code looks —
a repo-root `skills/` folder is discovered by nothing and every frontmatter field in it is
silently inert. Don't "tidy" them back out. If a new skill doesn't appear, run
**`/reload-skills`** (v2.1.152+) rather than restarting.

**Review checklists** live in `.ai/05-domains/`, phrased as questions rather than prescriptions
so they carry to any project and leave judgement intact. All `convention`.
