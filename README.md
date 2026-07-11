# Adaptive Self-Correcting Workflow (`workflow-core`)

[![tests](https://github.com/momomozakiki/ai-self-correcting-workflow/actions/workflows/tests.yml/badge.svg)](https://github.com/momomozakiki/ai-self-correcting-workflow/actions/workflows/tests.yml)

A disciplined meta-framework for AI-assisted development. It combines **fixed
safety invariants**, **per-task dynamic planning**, **conditional documentation
updates**, a **filesystem-native change-history ledger**, **source provenance**,
and a **closed-loop improvement cycle** — all pulled from this single, versioned
repository so every adopting project shares one source of truth for *process*.

> *Fixed invariants for safety; dynamic planning for agility; hooks for ambient
> awareness; history for accountability; provenance for trust; one workflow to
> rule them all.*

Full reference: **[`GUIDE.md`](GUIDE.md)** · Agent manual:
**[`skills/adaptive-workflow/SKILL.md`](skills/adaptive-workflow/SKILL.md)**

## What's here

```
workflow-core/
├── GUIDE.md                     # Full workflow reference (v4.4)
├── CHANGELOG.md · ROADMAP.md · CONTRIBUTING.md
├── history/FORMAT.md            # This repo's own change-history ledger
├── hooks/workflow_hook.py       # Fail-soft hook dispatcher (stdlib only)
├── skills/adaptive-workflow/    # Agent process manual (SKILL.md)
├── schemas/                     # config_schema.json + hook_contract.md
├── docs/                        # Documentation Standard refs (Progressive Disclosure Guide, etc.)
├── templates/                   # What adopting projects copy in
│   └── docs/                    #   DOC · CHANGELOG · SCOPE templates
└── tests/test_hook.py           # Synthetic-event tests (unittest)
```

## Quick start — adopt in a project

1. Add this repo as a submodule:
   `git submodule add <this-repo-url> .claude/workflow-core`
2. Copy `templates/workflow_config.json` → `.claude/workflow_config.json`, adjust
   paths and feature flags.
3. Merge `templates/settings.json.hooks` into `.claude/settings.json`.
4. Include `templates/CLAUDE.md.fragment` in your project's `CLAUDE.md`.
5. Initialize the ledger:
   `mkdir history && cp .claude/workflow-core/templates/history/FORMAT.md history/`

The `workflow_config.json` maps generic concepts (source dirs, ledger dir,
roadmap file, tool paths) to your project. Validate it against
[`schemas/config_schema.json`](schemas/config_schema.json).

## Keeping up to date (for adopters)

The workflow is a living system — updates land here and every adopting project
inherits them on its next sync.

**Pull the latest (submodule adopters):**

```bash
git -C .claude/workflow-core fetch origin
git -C .claude/workflow-core checkout main
git -C .claude/workflow-core pull --ff-only origin main
git add .claude/workflow-core            # stage the new submodule pointer
git commit -m "chore: update workflow-core to latest"
python -m unittest discover -s .claude/workflow-core/tests   # sanity-check
```

**Get notified automatically (F5, opt-in).** Enable the daily update check so
`SessionStart` tells you when you're behind — it fetches at most once per day and
**never auto-applies** (you run the commands above when ready). Add to your
`workflow_config.json`:

```json
"workflow_update_check": {
  "enabled": true,
  "submodule_path": ".claude/workflow-core",
  "remote": "origin",
  "branch": "main"
}
```

**Vendored (copied, no submodule)?** Re-copy the changed files (`hooks/`,
`schemas/`, `skills/`, `GUIDE.md`, `CONTRIBUTING.md`, `templates/`,
`.github/ISSUE_TEMPLATE/`), or migrate to the submodule model per
[`GUIDE.md`](GUIDE.md) §8.1.

**Found a flaw?** Report it upstream — open a *Workflow bug / flaw report* issue
(works even for vendored copies), or submit a fix per criticality. See
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## The hook

`hooks/workflow_hook.py` is a single fail-soft dispatcher for three events:

| Event | Does |
|-------|------|
| `SessionStart` | Injects git status, environment checks, the next roadmap action, and — when `workflow_update_check.enabled` — an opt-in daily update check (F5). |
| `PostToolUse` (`Edit\|Write\|MultiEdit`) | Tracks source/ledger edits; nudges once if source changed without docs. |
| `Stop` | Reminds you to commit and to log the ledger (bounded by `stop_hook.max_blocks`); on a dirty tree, records a `plans/UNFINISHED.md` breadcrumb so an interrupted closure is never lost. |

It uses **stdlib only** and always exits 0, so a workflow bug never breaks a
session. Contract: [`schemas/hook_contract.md`](schemas/hook_contract.md).

## Run the tests

```bash
python -m unittest discover -s tests
```

The same suite runs in CI on every push and pull request across Linux and
Windows (Python 3.9 and 3.12) — see
[`.github/workflows/tests.yml`](.github/workflows/tests.yml).

## Contributing

This workflow dogfoods itself — this repo runs its own hooks and keeps its own
ledger under `history/`. Improvements flow back upstream; see
[`CONTRIBUTING.md`](CONTRIBUTING.md).
