# Changelog

All notable changes to the workflow itself are recorded here. The workflow uses
[Semantic Versioning](https://semver.org/): breaking changes to the hook
contract, config schema, or mandatory invariants bump the major/minor version
and are called out so adopting projects can adjust their `workflow_config.json`.

## [Unreleased]

### Changed — BREAKING

- **The dispatcher moved to `.claude/hooks/workflow_hook.py`. Action required for
  every existing adopter.** It previously lived at `hooks/workflow_hook.py`, one
  level below the repository root. The script is unchanged in behaviour, but the
  path in your `.claude/settings.json` now points at a file that does not exist.

  **Why this breaks silently-ish.** Your settings file is yours — pulling the
  `workflow-core` submodule moves the script but cannot edit your config. When the
  command is missing, Claude Code reports a hook error in the transcript and
  **the tool call proceeds anyway** (per the hooks reference, any exit code other
  than 2 is a non-blocking error). So there *is* a visible notice, but it is easy
  to dismiss, and the important part is invisible: the four Tier-0 prohibitions
  keep declaring themselves `live` in `.ai/02-market-rules/prohibitions/` while
  nothing enforces them.

  **To fix — edit, do not copy.** In `.claude/settings.json`, replace every
  occurrence of

  ```
  $CLAUDE_PROJECT_DIR/.claude/workflow-core/hooks/workflow_hook.py
  ```

  with

  ```
  $CLAUDE_PROJECT_DIR/.claude/workflow-core/.claude/hooks/workflow_hook.py
  ```

  There are four (`SessionStart`, `PreToolUse`, `PostToolUse`, `Stop`). Note the
  doubled `.claude/` — the submodule now carries its own `.claude/` directory.
  If you also set `source_directories` in `workflow_config.json` to include
  `hooks`, change it to `.claude/hooks`.

  **Then verify, don't assume.** Ask Claude to run `rm -rf history/`. The guard
  must refuse it with a `Tier-0 prohibition-delete-ledger` message. If the command
  is merely queued for your approval with no such message, the hook is not wired —
  recheck the path. You can also run
  `python .claude/workflow-core/.claude/hooks/workflow_hook.py --self-test`, which
  must print `RESULT: PASS` **and** a line reading
  `[ ok ] config valid against schemas/config_schema.json`. A `validation skipped`
  warning there means the schema is unreachable and the check is not running.

### Fixed

- **`--self-test` reported `RESULT: PASS` while validating nothing.** The config
  schema was located as `__file__.parent.parent / "schemas"`, which assumed the
  dispatcher sat exactly one directory below the repository root. The move above
  broke that assumption, and because an unreachable schema only *warns*, the
  self-test kept exiting 0 with two knowingly-invalid configs passing. Replaced
  with `find_schema_path()`, an upward walk matching `find_config_path()`, so it
  resolves under both this repo's layout and an adopter's nested submodule.
  Regression covered by `tests/test_hook.py::TestSchemaLocation`, which asserts on
  the positive "config valid against" line rather than the exit code — the exit
  code cannot distinguish "validated and passed" from "skipped and defaulted to
  passing", which is exactly how this hid.
- **Adopters had no Tier-0 guard. Action required if you installed before this
  release.** `templates/settings.json.hooks` — the fragment adopters merge into
  `.claude/settings.json` — registered `SessionStart`, `PostToolUse` and `Stop`
  but **no `PreToolUse` block**, and no `permissions.defaultMode`. `PreToolUse` is
  the only event the guard runs on, so in every adopting project a force-push to a
  protected branch was not denied, deleting `history/` or `plans/archive/` was not
  denied, and history rewrites and heredocs never asked — while `CLAUDE.md`,
  `GUIDE.md` §7 and `.ai/02-market-rules/prohibitions/*.json` all declared those
  four prohibitions `live`. Measured before the fix: **0 of 3** Tier-0 probes
  denied under the template, 3 of 3 under this repo's own settings.

  **To fix an existing install — merge, do not copy:** open your
  `.claude/settings.json`, add the `PreToolUse` entry from
  `templates/settings.json.hooks` (matcher `Bash|PowerShell`, pointing at
  `$CLAUDE_PROJECT_DIR/.claude/workflow-core/.claude/hooks/workflow_hook.py`), and add
  `"defaultMode": "plan"` under `permissions`. Do **not** copy the file over your
  settings — it is a fragment, and overwriting discards your own permissions, env
  and any other hooks.

  **Then verify, don't assume:** attempt `git push --force` to your main branch and
  confirm it is **denied**. If it is allowed, the merge did not take.

  `tests/test_governance_library.py::SettingsWiring` now checks both the repo's
  settings and the adopter template; previously it read only the former, which is
  why a shipped config with no guard stayed green.
- **The skills now live where Claude Code discovers them.** `skills/` →
  `.claude/skills/`. Claude Code loads skills from `~/.claude/skills/`, a project
  `.claude/skills/` (plus nested ones below the working directory) and plugin
  directories, and from nowhere else — there is no setting that registers an
  alternative root. The skills at the repo root were therefore never loaded *as
  skills*: no `/adaptive-workflow` command existed, no `description` ever triggered
  an automatic load, and the `disallowed-tools: AskUserQuestion` on
  `autonomous-task` was inert. They worked only because `CLAUDE.md` named their
  file paths in prose.
  **Adopters must act:** copy `templates/skills/*` into your own `.claude/skills/`
  (the submodule's copy is not discovered from `.claude/workflow-core/`), and
  restart Claude Code once if `.claude/skills/` is new. See the updated
  `templates/CLAUDE.md.fragment`.

- **`.claude/settings.local.json` is now in the repo's `.gitignore`.** It was untracked
  only because of a machine-global git ignore rule, which no clone inherits — on any
  other checkout `git add -A` would commit your personal permission grants.
- **Corrected two wrong statements shipped in the previous release.**
  `disallowed-tools` **does** have a documented version floor — v2.1.152 (27 May 2026) —
  recorded here previously as "no documented minimum" because the skills docs page states
  none. Floors live in the release notes. The same release added **`/reload-skills`**, so
  the "restart Claude Code" advice for a skills directory the watcher missed is superseded;
  restart is now only the fallback.

### Added
- **`claude-code-layout` skill and `tests/test_claude_layout.py`.** Where Claude Code
  configuration must live to be loaded at all, and a test that enforces it. The organising
  distinction: `skills/`, `agents/`, `commands/`, `output-styles/`, `rules/` and
  `workflows/` are **discovered by location** — put them elsewhere and they are inert —
  while **hooks are registered** in `settings.json`, so their scripts may live anywhere but
  a missing registration makes them unreachable. Note there is no `.claude/hooks/`
  discovery; a `hooks/hooks.json` file is plugin structure, and following third-party
  guides that claim otherwise will silently unwire your guard.
- **`SessionStart` now emits `reloadSkills`** when `.claude/skills/` exists, so a skill
  added between sessions is picked up without a restart. **`PostToolUse` emits a one-time
  skill advisory** when a file under `.claude/skills/` is edited. Both advisory; new state
  key `skill_nudged` (see `schemas/hook_contract.md`).
- **`skill-authoring` skill and `tests/test_skills.py`.** The authoring rules —
  discovery locations, the progressive-disclosure layout, naming, and the verified
  frontmatter reference — plus a stdlib-only test that enforces them: entrypoint
  presence and casing, kebab-case names, `name`/directory agreement, description
  length, the documented 500-line body cap, unknown frontmatter keys (an
  unrecognised key is ignored silently at runtime), markdown link resolution, the
  old path staying gone, and `templates/skills/` parity. It warns past a
  ~5,000-token proxy, measured in characters rather than lines, because
  auto-compaction re-attaches only the first 5,000 tokens of each skill. 15 of its
  25 tests are negative controls asserting the named violation each defect produces.
- **`.ai/05-domains/rule-skill-authoring-review.json`** (8 items, `convention`),
  harvested from the defect above per `GROWTH.md`, and mirrored into
  `templates/ai-library/`.
- **`adaptive-workflow` split** into a 183-line `SKILL.md` plus three
  `references/` (conditional triggers and the ledger, the Documentation Standard,
  upstream contribution), so it stays inside the compaction budget as it grows.
- **Governance library (`.ai/`) and the v14 integration.** Instantiated the
  imported Self-Growing Checklist Ecosystem v14 as a chunked rule library, with an
  adopter scaffold at `templates/ai-library/`. Every artifact declares an
  `enforcement_status` — `live` (a hook or test enforces it), `convention`
  (followed, nothing blocks), or `declarative` (recorded only, not enforceable on
  Claude Code + a Claude Pro subscription with no API key). Declarative fields are
  written as `null` with a reason rather than filled with plausible fakes.
  `docs/governance-integration-decision.md` dispositions all 24 v14 sections and
  records the runtime assumptions and source verification behind the tiering.
  New `GUIDE.md` §12 (21-step → Phase 0–3 mapping), §13 (the library), §14
  (runtime assumptions).
- **Agent loop detection.** `PostToolUse` hashes `(tool_name, tool_input)` and
  flags consecutive identical calls at `loop_detection.repeat_threshold`
  (default 3, clamped to ≥2), logging one JSONL line per loop to
  `loop_detection.log_path`. Judged on arguments, not just the tool, so reading
  ten different files is work while reading one file ten times is a loop. Each
  signature is announced once per session; `Stop` reports the session total.
  Advisory only — it can't block, because the tool has already run. New config
  block `loop_detection`; new state keys `recent_tool_calls`, `loop_hits`.
- **`--self-test`.** Validates `workflow_config.json` against
  `schemas/config_schema.json` using a stdlib JSON Schema subset (no
  `jsonschema` dependency), runs workflow health checks, and derives a governance
  maturity level 1–5 written to `.ai/00-system/maturity-tracker.json`. **Exit code
  reflects validation only** — the maturity level is reported, never enforced. New
  config block `governance` (`library_root`, `maturity_tracker`).
- **`ANTHROPIC_API_KEY` warning** at `SessionStart` and in `--self-test`: a key in
  the environment overrides the Claude subscription and bills per token. Warning
  only, since API-key auth is legitimate.
- **Retrospective and the self-hardening loop.** `docs/RETROSPECTIVE.md` activates
  the previously unused `retrospective_file` config key. A mistake recorded twice
  is marked `(recurring)` and owes a rule file; `--self-test` reports uncodified
  recurrences and withholds maturity level 5 until none remain.
- **Optional `**Risk:**` field on ledger entries**, using five fixed slugs
  (`privilege`, `design`, `behavioral`, `structural`, `accountability`) drawn from
  the CISA / Five Eyes agentic-AI risk categories. The slugs are stable even if
  upstream prose renames a category. Convention only — nothing parses it.

### Changed
- **Documentation consolidated.** The imported v13/v14 framework (3,054 lines,
  ~96% duplicated) folded into `docs/self-growing-checklist-ecosystem/` per
  `GUIDE.md` §6.4 — five children each inside the ≤5,000-token Semantic budget,
  plus an `index.md` and a sibling `CHANGELOG.md` holding the v13→v14 delta.
  v13 retired; both flat files are recoverable from history (commit `6470a2c`).
  `docs/claude-code-hook-integration.md` folded into a folder for the same reason
  (its revision table passed ~8 rows) and bumped to v1.13.
- **State-key list de-duplicated.** `schemas/hook_contract.md` is now the only
  place it is maintained; the integration guide points at it instead of restating.
- Removed the orphaned `docs/Adaptive Self‑Correcting Workflow.md` redirect stub —
  a pointer to `GUIDE.md` with no inbound links, marked "never load for content".
- `GUIDE.md` → **5.0**. Phase 0 gains a Tier-0 prohibitions block; Phase 2 gains
  reversibility, loop-awareness and a no-heredoc-stdin guard; Phase 3 gains the
  retrospective step.
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
- `.claude/hooks/workflow_hook.py` — fail-soft, stdlib-only dispatcher for
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
