# Changelog

All notable changes to the workflow itself are recorded here. The workflow uses
[Semantic Versioning](https://semver.org/): breaking changes to the hook
contract, config schema, or mandatory invariants bump the major/minor version
and are called out so adopting projects can adjust their `workflow_config.json`.

## [Unreleased]

### Added
- **`main_branch` auto-detection.** The `Stop` hook no longer assumes the default
  branch is `main`: `resolve_main_branch()` reads the local ref
  `refs/remotes/<remote>/HEAD` (via `git symbolic-ref` — no network), so
  `master`/`trunk`/`develop` repos stop getting a spurious commit reminder on
  every close. New `stop_hook` keys: `main_branch_autodetect` (default **true**),
  `main_branch_remote` (default `origin`), and `main_branch_probe_remote`
  (default **false** — opt-in `git remote show` fallback, which contacts the
  remote). An explicit `stop_hook.main_branch` still wins over detection, so
  existing configs behave exactly as before; the result is memoised in the new
  `main_branch_detected` state key so a session probes git at most once.
  Documented in `GUIDE.md` §7.4, `docs/claude-code-hook-integration.md` §3.4, and
  `schemas/hook_contract.md`.
- **Stop-hook Phase-3 auto-breadcrumb.** When the working tree is dirty at
  session end (any branch), the `Stop` hook records `plans/UNFINISHED.md`
  (branch, uncommitted files, pending closure steps) so an interrupted closure
  survives a force-close and is surfaced by the next `SessionStart` (F4). It is
  marker-guarded (`<!-- workflow-hook: auto-breadcrumb -->`) and never overwrites
  a human-authored `UNFINISHED.md`.
- **Opt-in F5 daily update check** in `SessionStart`. New
  `workflow_update_check` config block (`enabled` default **false**,
  `submodule_path`, `remote`, `branch`): when enabled, fetches the vendored
  `workflow-core` submodule at most once/day (gated by `.ai/.workflow_check_date`)
  and injects a `🔄 Workflow updates available` notice if behind. Detection-only —
  never runs `git submodule update`. Added to `schemas/config_schema.json` and
  the config templates.
- `.github/ISSUE_TEMPLATE/workflow-bug.yml` + `config.yml` — a bug-report path
  for adopters who vendored the files (no submodule/PR access), with a
  criticality dropdown and version field.
- `.github/workflows/tests.yml` — GitHub Actions CI running
  `python -m unittest discover -s tests` on every push and pull request across a
  matrix of `ubuntu-latest` + `windows-latest` × Python 3.9 and 3.12. No install
  step: the suite is dependency-free (stdlib only), so CI runs exactly what
  adopters run locally. README carries a live status badge.

### Changed
- Clarified severity vocabulary: the top tier **High** is a.k.a. **Critical**
  (there is no tier above it) — `CONTRIBUTING.md`, `GUIDE.md` §10, `SKILL.md`.

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
