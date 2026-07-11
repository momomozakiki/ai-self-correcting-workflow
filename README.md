# Adaptive Self-Correcting Workflow (`workflow-core`)

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

## The hook

`hooks/workflow_hook.py` is a single fail-soft dispatcher for three events:

| Event | Does |
|-------|------|
| `SessionStart` | Injects git status, environment checks, and the next roadmap action. |
| `PostToolUse` (`Edit\|Write\|MultiEdit`) | Tracks source/ledger edits; nudges once if source changed without docs. |
| `Stop` | Reminds you to commit and to log the ledger — bounded by `stop_hook.max_blocks`. |

It uses **stdlib only** and always exits 0, so a workflow bug never breaks a
session. Contract: [`schemas/hook_contract.md`](schemas/hook_contract.md).

## Run the tests

```bash
python -m unittest discover -s tests
```

## Contributing

This workflow dogfoods itself — this repo runs its own hooks and keeps its own
ledger under `history/`. Improvements flow back upstream; see
[`CONTRIBUTING.md`](CONTRIBUTING.md).
