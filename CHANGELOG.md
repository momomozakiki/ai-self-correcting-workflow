# Changelog

All notable changes to the workflow itself are recorded here. The workflow uses
[Semantic Versioning](https://semver.org/): breaking changes to the hook
contract, config schema, or mandatory invariants bump the major/minor version
and are called out so adopting projects can adjust their `workflow_config.json`.

## [Unreleased]

### Added
- `.github/workflows/tests.yml` — GitHub Actions CI running
  `python -m unittest discover -s tests` on every push and pull request across a
  matrix of `ubuntu-latest` + `windows-latest` × Python 3.9 and 3.12. No install
  step: the suite is dependency-free (stdlib only), so CI runs exactly what
  adopters run locally. README carries a live status badge.

## [4.1.0] — 2026-07-10

Initial implementation of the v4.1 design as a working `workflow-core` repository.

### Added
- `hooks/workflow_hook.py` — fail-soft, stdlib-only dispatcher for
  `SessionStart`, `PostToolUse`, and `Stop`, with per-session state, environment
  checks (honoring `null` version flags), roadmap next-action parsing, doc
  nudges, and bounded Stop reminders. Config discovery prefers
  `$CLAUDE_PROJECT_DIR` with a walk-up fallback. Supports `--dry-run`.
- `tests/test_hook.py` — 16 synthetic-event tests (`unittest`).
- `schemas/config_schema.json` (adds optional `stop_hook.main_branch`) and
  `schemas/hook_contract.md`.
- `templates/` — `workflow_config.json`, `settings.json.hooks`,
  `CLAUDE.md.fragment`, `history/FORMAT.md`.
- `skills/adaptive-workflow/SKILL.md` — the agent operating manual.
- `GUIDE.md` (promoted from the design doc), `ROADMAP.md`, `CONTRIBUTING.md`,
  `README.md`, and `history/FORMAT.md`.
- Self-adoption: `.claude/workflow_config.json`, `.claude/settings.json`,
  `CLAUDE.md`, and the first ledger entry — this repo runs its own workflow.
