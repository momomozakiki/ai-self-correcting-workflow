---
title: Claude Code Hook Integration
version: 1.9
last_validated: 2026-07-18
official: false
source: agent-generated, describing this repo's own hooks/workflow_hook.py; hook-contract facts cross-checked against https://code.claude.com/docs/en/hooks
tags: [hooks, claude-code, integration, workflow, dispatcher]
applies_when: "Wiring up, understanding, or adapting the workflow hook dispatcher for a Claude Code project."
estimated_tokens: 5000
---

# Claude Code Hook Integration
*Adaptive Self‑Correcting Workflow – Implementation Guide*
**Version 1.9** — *Describes the dispatcher shipped in this repo; doubles as a golden reference for adopters*
**Last Validated**: 2026‑07‑18

## Revision History
| Version | Date       | Change                                                                                                 |
|---------|------------|--------------------------------------------------------------------------------------------------------|
| 1.9     | 2026-07-18 | Added §5.1.1 documenting the `permissions.allow` allowlist that stops plan mode from prompting on every read-only `Bash` command. |
| 1.8     | 2026-07-10 | Migrated to the unified Documentation Standard: SOURCE-PROVENANCE comment → YAML frontmatter; changelog moved from the comment's `Notes:` field into this table. |
| 1.7     | 2026-07-10 | Realigned the guide with the real Python dispatcher and this repo's actual `.claude/workflow_config.json`; established as the golden reference for adopters. |
| 1.6     | (prior)    | Described a different (Flutter/Dart) project — superseded.                                              |
| ≤ 1.3   | (prior)    | Described a hypothetical Node.js design — superseded.                                                   |

> This guide describes the **real** implementation in this repository — a single
> stdlib‑Python dispatcher, [`hooks/workflow_hook.py`](../hooks/workflow_hook.py),
> driven by [`.claude/workflow_config.json`](../.claude/workflow_config.json) and
> wired up in [`.claude/settings.json`](../.claude/settings.json). Every config
> snippet and behavioural claim below is taken from those live artifacts, so the
> doc works both as this repo's reference **and** as a golden template other
> repos adapt (see [§5.3 Adapting for your repo](#53-adapting-for-your-repo)).
> [`schemas/hook_contract.md`](../schemas/hook_contract.md) is the authoritative
> I/O contract.

---

## Overview

Three Claude Code hook events augment the Adaptive Self‑Correcting Workflow by
providing **ambient awareness** — injecting context at session start, nudging
about docs/ledger drift after edits, and reminding about Phase‑3 closure before
the session ends.

**All hooks are advisory.** They inject context and, at `Stop`, may ask the agent
to continue — but blocking is bounded by a configurable cap and the agent stays
in control. A bug in the tooling can never break a session: the dispatcher is
**fail‑soft** and always exits `0`.

---

## Hook Events Used

| Hook Event | When It Fires | Purpose in Workflow |
|------------|---------------|----------------------|
| **`SessionStart`** | When a session begins or resumes | Reset per‑session state, report git status, run env checks, surface the roadmap next‑action, flag an unfinished plan |
| **`PostToolUse`** | After an `Edit`/`Write`/`MultiEdit` succeeds | One‑time advisory nudge if source changed without docs/ledger |
| **`Stop`** | When Claude finishes a response | Bounded Phase‑3 closure reminders (dirty tree, missing ledger entry) |

---

## Implementation Architecture

A **single Python dispatcher** ([`hooks/workflow_hook.py`](../hooks/workflow_hook.py))
serves all three events. It reads the event JSON from `stdin`, branches on
`hookEventName` (`hook_event_name` is also accepted), and writes a JSON response
to `stdout`. It:

- Discovers `workflow_config.json` via `$CLAUDE_PROJECT_DIR` first, then a
  walk‑up fallback — so it works whether vendored as a submodule or run in‑repo.
- Maintains a per‑session state file (`{tempdir}/workflow_hook_state_<id>.json`)
  with atomic writes (`os.replace`) — see [§4](#4-state-persistence-persession).
- Swallows every exception and exits `0` (**fail‑soft**).
- Uses only the Python standard library (3.8+) — no `pip install` step.

---

## 1. `SessionStart` Hook

### 1.1 Trigger & Matchers
- **Event**: `SessionStart`
- **Matcher**: Optional (`startup`, `resume`, `clear`, `compact`). This repo omits
  the matcher, so the handler runs on every start.
- **Input (stdin JSON)** — common fields:

```json
{
  "session_id": "uuid",
  "transcript_path": "/path/to/transcript.json",
  "cwd": "/project/root",
  "permission_mode": "default",
  "hook_event_name": "SessionStart"
}
```

> `SessionStart` runs **before MCP servers finish connecting**; the dispatcher
> relies only on the filesystem and `git`, never MCP tools.

### 1.2 Output

All fields go **inside `hookSpecificOutput`** (`sessionTitle` is **not** a
top‑level field):

| Field | Location | Description |
|-------|----------|-------------|
| `additionalContext` | `hookSpecificOutput` | Injected into the session before the first prompt |
| `sessionTitle` | `hookSpecificOutput` | Names the session (like `/rename`); applied for `startup`/`resume` |
| `initialUserMessage` | `hookSpecificOutput` | First user message (non‑interactive `-p` mode) |
| `watchPaths` | `hookSpecificOutput` | Absolute paths to watch for `FileChanged` events |
| `reloadSkills` | `hookSpecificOutput` | Re‑scan skill directories after the hook completes |

The dispatcher emits `additionalContext` + a static `sessionTitle`:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "## Adaptive Workflow — session start\n\nGit: branch `main` …",
    "sessionTitle": "Adaptive Workflow session"
  }
}
```

### 1.3 What the handler does

`handle_session_start()`:

1. Purges stale per‑session state files (> 24h) and resets state for this session.
2. Reports **git status** — branch, dirty flag (F1 nudge), and ahead/behind vs.
   the upstream.
3. Runs the **env checks** in `workflow_config.json → env_check.tool_paths`
   (F2). A `version_flag` of `null`/`""` means "check existence only"; otherwise
   it runs `<path> <version_flag>` and reports the first output line.
4. Parses the roadmap's `**Next action:**` line (F4) from `roadmap_file`
   (repo‑root `ROADMAP.md` here). The marker must start the line (after optional
   whitespace, `>` or a list bullet) so inline prose can't false‑match.
5. Flags `plans/UNFINISHED.md` if present (F4).
6. Appends a static reminder about the weekly ledger and adding doc frontmatter
   (provenance + version) to new docs.

`sessionTitle` is the constant string `"Adaptive Workflow session"`.

---

## 2. `PostToolUse` Hook — Documentation & Ledger Nudge

### 2.1 Trigger & Matchers
- **Event**: `PostToolUse`
- **Matcher (in settings.json)**: `Edit|Write|MultiEdit`. `Bash` is **not**
  matched — a generic shell command doesn't reliably reveal which files it
  touched; the source‑change signal is reconciled at `Stop` instead.
- **Input (stdin JSON)**:

```json
{
  "session_id": "uuid",
  "hook_event_name": "PostToolUse",
  "tool_name": "MultiEdit",
  "tool_input": {
    "file_path": "hooks/a.py",
    "edits": [ { "file_path": "hooks/b.py" } ]
  },
  "tool_response": { }
}
```

Both the top‑level `file_path` and every `edits[].file_path` are collected by
`collect_touched_paths()`.

### 2.2 Output

`PostToolUse` **cannot block** — the tool has already run. The dispatcher emits
an advisory only when it has something to say:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Consider updating docs and the weekly ledger …"
  }
}
```

Otherwise it produces no output.

> *By design, advisory only.* Claude Code does allow `PostToolUse` to return a
> top‑level `decision: "block"` + `reason` to force Claude to react. This
> workflow deliberately **does not** — the nudge is a soft signal, and forcing a
> response on every edit would undercut agent autonomy. Non‑negotiable closure
> gates belong in the `Stop` hook (§3).

> *MCP caveat:* `additionalContext` is reliable for native tools. For MCP tool
> calls it may not always be appended — but note this repo's matcher only fires
> on `Edit|Write|MultiEdit`, so it isn't affected.

### 2.3 What the handler does

`handle_post_tool_use()` classifies each touched path against the config's
`source_directories`, `documentation_directories`, and `ledger.directory`,
persisting `source_changed` / `ledger_touched` flags in the session state file.
If source changed, no doc was touched on this call, and no nudge has fired yet
this session, it emits a **one‑time** advisory. The `doc_nudged` flag guards
against repetition.

---

## 3. `Stop` Hook — Phase‑3 Closure Reminder

### 3.1 Trigger & Matchers
- **Event**: `Stop`
- **Matchers**: None — `Stop` does not support matchers; omitting `matcher` is
  correct.
- **Input (stdin JSON)**:

```json
{
  "session_id": "uuid",
  "hook_event_name": "Stop",
  "stop_hook_active": false
}
```

`stop_hook_active` appears when the hook is re‑invoked after a previous block; the
dispatcher honours it to avoid infinite blocking.

### 3.2 Output — Blocking Behavior

To ask the agent to keep working, return a **top‑level** `decision`/`reason`
(there is **no** `hookSpecificOutput` for `Stop`; all instruction goes in
`reason`):

```json
{
  "decision": "block",
  "reason": "Working tree is dirty on branch `feat/x` … commit & push before ending."
}
```

Guards against an infinite block loop:

- **`continue: false` precedence** — if a response sets both `decision: "block"`
  and `continue: false`, `continue: false` wins and the turn ends. To block you
  must set `continue: true` or omit it. The dispatcher omits it.
- **Config cap** — the dispatcher stops re‑blocking once
  `stop_block_count >= stop_hook.max_blocks` (default 2).
- **`stop_hook_active`** — if set, the dispatcher exits `0` immediately.
- **Platform cap** — Claude Code itself ends the turn after **8 consecutive
  blocks**.

### 3.3 What the handler does

`handle_stop()` reads the **session state file** (not `git diff HEAD`, which would
include pre‑session changes). It short‑circuits (exit `0`) if `stop_hook_active`
is set or `stop_block_count >= max_blocks`. Otherwise it assembles reminders when:

1. the working tree is **dirty on a non‑`main_branch` branch** → commit & push
   (`git add -A && git commit && git push`), and/or
2. `source_changed` **and not** `ledger_touched` → add a weekly‑ledger entry
   (`history/YYYY-Www.md`, What / Why / Refs).

If any reminder applies (and the caps allow), it increments `stop_block_count`,
saves state, and emits the block. Otherwise it exits `0` and the session ends.

---

## 4. State Persistence (Per‑Session)

State lives at:

```
{tempfile.gettempdir()}/workflow_hook_state_<sanitized_session_id>.json
```

**Fields** (see `default_state()`):

- `source_changed` — a source‑directory file was edited this session.
- `ledger_touched` — a file under `ledger.directory` was edited this session.
- `doc_nudged` — the one‑time `PostToolUse` advisory has fired.
- `stop_block_count` — number of `Stop` blocks emitted this session.
- `session_start_ts` — creation timestamp (used for stale purging).

**Atomic writes**: written to a temp sibling then `os.replace`d into place.
**Cleanup**: on `SessionStart`, state files older than 24h are deleted. If
`session_id` is absent, the dispatcher runs statelessly.

---

## 5. Configuration

### 5.1 `.claude/settings.json`

Claude Code requires a **two‑level** structure per event: a *matcher‑group* array,
each entry containing a `hooks` array of `{ type, command }` handlers. A flat
`{ "type", "command", "matcher" }` entry directly inside the event array is
**invalid** and silently fails to register. This is the shape actually shipped in
[`.claude/settings.json`](../.claude/settings.json):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/hooks/workflow_hook.py\"" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/hooks/workflow_hook.py\"" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python \"$CLAUDE_PROJECT_DIR/hooks/workflow_hook.py\"" }
        ]
      }
    ]
  }
}
```

- The same script serves all three events; it self‑identifies via `hookEventName`.
- The `matcher` sits on the **group object**, not the handler. `PostToolUse`
  filters to `Edit|Write|MultiEdit`; `SessionStart` and `Stop` have no matcher
  (`Stop` doesn't support one).

#### 5.1.1 Permissions — reducing plan‑mode approval prompts

With **no `permissions` block**, Claude Code prompts for approval on every
`Bash` command by default. Plan mode blocks the `Edit`/`Write`/`MultiEdit`
tools but does **not** auto‑approve `Bash` — the harness can't know an arbitrary
shell command is read‑only (a `Bash` call can redirect to a file, `sed -i`,
`rm`, …), so it deliberately still asks. The result is that Phase‑0/planning
commands (`git status`, `git log`, `git fetch`, `python -m unittest`) each
trigger a prompt.

The fix is an **allowlist** of the read‑only commands the workflow actually
runs, added alongside `hooks` in [`.claude/settings.json`](../.claude/settings.json):

```json
{
  "permissions": {
    "allow": [
      "Read", "Grep", "Glob",
      "Bash(git status:*)", "Bash(git log:*)", "Bash(git diff:*)",
      "Bash(git fetch:*)", "Bash(git pull:*)", "Bash(git branch:*)",
      "Bash(git remote:*)", "Bash(git rev-parse:*)", "Bash(git show:*)",
      "Bash(python -m unittest:*)", "Bash(python --version)",
      "Bash(cat:*)", "Bash(ls:*)"
    ]
  },
  "hooks": { "…": "…" }
}
```

- All entries are read‑only except `git fetch`/`git pull` — the workflow's
  sanctioned Phase‑0 sync (F1), safe to allow.
- **Extend it** with your project's own read‑only commands (linters, test
  runners, package managers). Run the `/fewer-permission-prompts` skill to
  auto‑scan transcripts and generate an allowlist from commands you actually use.
- Do **not** use `bypassPermissions` to silence prompts — it removes them in
  *every* mode, not just planning, and defeats plan mode's safety. Prefer
  project `.claude/settings.json` for team‑shared rules, or
  `.claude/settings.local.json` for personal, un‑committed ones.

### 5.2 `.claude/workflow_config.json`

The dispatcher reads this on every invocation (changes take effect immediately).
This is the live config for this repo:

```json
{
  "project_root": "..",
  "roadmap_file": "ROADMAP.md",
  "ledger": {
    "enabled": true,
    "directory": "history"
  },
  "source_directories": ["hooks", "skills", "schemas", "templates"],
  "documentation_directories": ["docs"],
  "env_check": {
    "tool_paths": {
      "python": {
        "path": "python",
        "version_flag": "--version"
      }
    }
  },
  "stop_hook": {
    "max_blocks": 2,
    "main_branch": "main"
  }
}
```

### 5.3 Adapting for your repo

To adopt this as a golden template, change these keys to match your project;
the dispatcher and contract stay the same:

| Key | What to set it to |
|-----|-------------------|
| `project_root` | Relative path from the config file to your repo root (`".."` when the config is under `.claude/`). |
| `source_directories` | Directories that count as "source" for the doc/ledger nudge (e.g. `["src"]`, `["lib"]`). |
| `documentation_directories` | Directories that count as "docs" (e.g. `["docs"]`). |
| `roadmap_file` | Path (from repo root) to the roadmap holding the `**Next action:**` line. |
| `ledger.directory` | Where weekly ledger files (`YYYY-Www.md`) live. |
| `env_check.tool_paths` | Tools to verify at `SessionStart`. Each entry is `{ "path", "version_flag" }`; use `null`/`""` for an existence‑only check. Add your runtimes (node, go, …). |
| `stop_hook.main_branch` | The branch on which a dirty tree is *not* nagged (commits there are expected to be intentional). |
| `stop_hook.max_blocks` | How many times `Stop` may re‑block before giving up (default 2). |

> **`$CLAUDE_PROJECT_DIR`** in the `command` is provided by Claude Code and
> expands to the project root, so the path resolves regardless of the session's
> working directory. Vendoring the hook as a submodule? Point the command at the
> vendored path (e.g. `.claude/workflow-core/hooks/workflow_hook.py`) — config
> discovery still finds `workflow_config.json` via `$CLAUDE_PROJECT_DIR`.

---

## 6. Deployment Checklist

1. **Python availability**: ensure `python` (3.8+) is on the `PATH` where Claude
   Code runs. If a version manager hides it, use an absolute path in `command`.
   The dispatcher is stdlib‑only — no `pip install`.
2. **File permissions**: `hooks/workflow_hook.py` must be readable; it need not be
   executable (invoked via `python`).
3. **Git**: the hook runs `git`; ensure it's installed and the `cwd` is a repo.
   Missing git degrades to notes rather than errors.
4. **Config present**: `workflow_config.json` must be discoverable (via
   `$CLAUDE_PROJECT_DIR`, `.claude/`, or a walk‑up). Missing config degrades to
   defaults rather than erroring.
5. **Testing**:
   - Start a session with `plans/UNFINISHED.md` present → the F4 flag appears.
   - Edit a source file without touching docs → the one‑time nudge fires (and
     does **not** fire again).
   - Make an uncommitted change on a feature branch and end the turn → the `Stop`
     reminder appears, then stops after `max_blocks`.
   - Run the suite: `python -m unittest discover -s tests`.

---

## 7. Summary of Validated Schemas

| Aspect | `SessionStart` | `PostToolUse` | `Stop` |
|--------|---------------|---------------|--------|
| **Matcher support** | ✅ (startup, resume, clear, compact) | ✅ (tool name) | ❌ None |
| **`additionalContext`** | ✅ inside `hookSpecificOutput` | ✅ inside `hookSpecificOutput` | ❌ Not supported; use `reason` |
| **`sessionTitle`** | ✅ inside `hookSpecificOutput` | ❌ | ❌ |
| **`watchPaths` / `reloadSkills`** | ✅ inside `hookSpecificOutput` | ❌ | ❌ |
| **Blocking decision** | ❌ N/A | ❌ (tool already ran) | ✅ top‑level `decision: "block"` + `reason` |
| **State persistence** | ✅ resets per‑session file | ✅ updates flags | ✅ reads flags + block count |
| **Block cap** | – | – | `max_blocks` (config) + 8 consecutive (platform) |
| **`continue: false` precedence** | – | – | Overrides `decision: "block"` |

---

## Official References

- [Claude Code Hooks – Official Documentation](https://code.claude.com/docs/en/hooks)
- Authoritative in‑repo contract: [`schemas/hook_contract.md`](../schemas/hook_contract.md)
- Behavioural spec: `GUIDE.md` §7

---

*End of Document – Implementation Guide v1.8*
