# CLAUDE.md

> **This repository _is_ `workflow-core`.** It defines the Adaptive
> Self-Correcting Workflow and dogfoods it: the hooks in `.claude/settings.json`
> point at this repo's own `hooks/workflow_hook.py` (there is no
> `.claude/workflow-core` submodule here — this is the source). We practice what
> we preach, keeping our own ledger under `history/`.

<!-- ==================================================================== -->
<!-- BEGIN adaptive-workflow fragment (managed by .claude/workflow-core)   -->
<!-- Included verbatim; project-specific notes go OUTSIDE this block.      -->
<!-- ==================================================================== -->

## Adaptive Self-Correcting Workflow

This project follows the Adaptive Self-Correcting Workflow. The full reference
lives in `GUIDE.md`; the agent operating manual is the `adaptive-workflow` skill
(`skills/adaptive-workflow/SKILL.md`). Hooks provide ambient reminders — treat
them as helpful nudges, not blockers.

### Tier 0 — absolute prohibitions (never overrideable)
- Never force-push a shared branch. Never commit secrets. Never rewrite published
  history. Never delete the ledger or the plan archive.
- Full set: `.ai/02-market-rules/prohibitions/`.
- **Three of these are enforced.** A `PreToolUse` guard (`hooks/workflow_hook.py`,
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

## Project-specific notes

- **Tests must stay dependency-free.** The hook is stdlib-only so adopters can
  vendor it without a dependency tree. Run: `python -m unittest discover -s tests`.
- When changing hook behaviour, update `schemas/hook_contract.md`, `GUIDE.md`
  §7, and `skills/adaptive-workflow/SKILL.md` together to prevent drift.
  `schemas/hook_contract.md` is the **only** place the state-key list lives.
- **Health check:** `python hooks/workflow_hook.py --self-test` validates the
  config and reports a governance maturity level. Exit code reflects validation
  only — the level is reported, never enforced.
- **Governance library** in `.ai/` (GUIDE §13). Every artifact declares
  `enforcement_status`: `live` (a hook or test enforces it), `convention` (followed,
  nothing blocks), `declarative` (recorded only). Never imply enforcement that
  doesn't exist — write declarative fields as `null` with a reason, never faked.
  `tests/test_governance_library.py` enforces this: `live` needs an `enforced_by`
  list resolving to real code, `convention` needs an `enforcement_note`. Any edit
  under `.ai/` must be mirrored into `templates/ai-library/` in the same commit.
- **Autonomous runs.** `skills/autonomous-task/SKILL.md` removes `AskUserQuestion` for the
  turn and says what to do instead: read the repo, then official docs, then take the
  conservative option and record the assumption. It ends by invoking `skills/handover/`,
  which writes `plans/HANDOVER.md` — the user's entire view of a run they didn't watch.
  Autonomy means not asking the user to arbitrate; it is **not** licence to click through
  a guard's `ask`.
- **Review checklists** live in `.ai/05-domains/`, phrased as questions rather than
  prescriptions so they carry to any project and leave judgement intact. All `convention`.
  `.ai/06-components/` stays empty until a pattern has shipped and survived review —
  `BLUEPRINT_SCHEMA.md` has the bar.
- **Runtime:** Claude Code on a Claude Pro subscription, no API key (GUIDE §14).
  Sonnet 5 for routine work, `/model opus` for hard passes. **Fable 5 bills usage
  credits on Pro — never make it a default.**
- **No heredoc stdin.** Write scripts to a file and run the file; use the editing
  tools for source changes. Escapes get mangled silently.
