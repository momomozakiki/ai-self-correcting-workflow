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

### Fixed invariants — always do first (Phase 0)
- **F1 Git sync:** `git fetch && git pull --rebase`. If the tree is dirty, ask
  the user how to proceed before changing anything.
- **F2 Environment:** verify the tools in `workflow_config.json → env_check`.
- **F3 Living docs:** load configured docs; flag any missing `SOURCE-PROVENANCE`.
- **F4 Unfinished plan / roadmap:** if `plans/UNFINISHED.md` exists, surface it
  immediately; note the next unchecked roadmap item.
- **F5 Daily workflow update check:** once per day (N/A here — this is the source).

### Per-task discipline
- **Plan (Phase 1):** design a task-specific checklist covering tests, doc
  updates, ledger entries, provenance, and roadmap impact.
- **Execute (Phase 2):** implement → run linter/tests → apply conditional
  triggers. **Log every intentional change** to the weekly ledger
  `history/YYYY-Www.md` (skip only trivial typo/whitespace-only edits). Add
  `SOURCE-PROVENANCE` to any new external document.
- **Close (Phase 3):** archive the plan, write the final ledger entry, update
  the roadmap, then commit & push. You are **not done** until `UNFINISHED.md`
  is cleared, the ledger entry is written, and the commit is pushed.

<!-- END adaptive-workflow fragment -->

## Project-specific notes

- **Tests must stay dependency-free.** The hook is stdlib-only so adopters can
  vendor it without a dependency tree. Run: `python -m unittest discover -s tests`.
- When changing hook behaviour, update `schemas/hook_contract.md`, `GUIDE.md`
  §7, and `skills/adaptive-workflow/SKILL.md` together to prevent drift.
