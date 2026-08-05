---
title: Claude Code Hook Integration
version: 1.13
last_validated: 2026-08-04
official: false
source: agent-generated, describing this repo's own hooks/workflow_hook.py; hook-contract facts cross-checked against https://code.claude.com/docs/en/hooks
tags: [hooks, claude-code, integration, workflow, dispatcher]
applies_when: "Wiring up, understanding, or adapting the workflow hook dispatcher for a Claude Code project."
estimated_tokens: 5000
---

# Claude Code Hook Integration
*Adaptive Self‑Correcting Workflow – Implementation Guide*
**Version 1.13** — *Describes the dispatcher shipped in this repo; doubles as a golden reference for adopters*
**Last Validated**: 2026‑08‑04

## Revision History
| Version | Date       | Change                                                                                                 |
|---------|------------|--------------------------------------------------------------------------------------------------------|
| 1.13    | 2026-08-04 | Loop detection (§2.4) and `--self-test` (§8) documented. §4's state-field list replaced by a pointer to `schemas/hook_contract.md`. Folded into a folder; history relocated. |
| 1.12    | 2026-08-04 | New §3.4: `main_branch` resolution order (explicit pin → local `refs/remotes/<remote>/HEAD` → opt-in `git remote show` → `main`). Adds the three `stop_hook.main_branch_*` keys to §5.2/§5.3 and `main_branch_detected` to §4. |
| 1.11    | 2026-07-18 | §3.2 Stop-reminder mirror: use the `git commit -m "<msg>"` form so an agent copying it can't hit a bare-`git commit` editor hang or a stdin/heredoc rejection. |

*Full history: [`CHANGELOG.md`](CHANGELOG.md).*

> This guide describes the **real** implementation in this repository — a single
> stdlib‑Python dispatcher, [`hooks/workflow_hook.py`](../../hooks/workflow_hook.py),
> driven by [`.claude/workflow_config.json`](../../.claude/workflow_config.json) and
> wired up in [`.claude/settings.json`](../../.claude/settings.json). Every config
> snippet and behavioural claim below is taken from those live artifacts, so the
> doc works both as this repo's reference **and** as a golden template other
> repos adapt (see [§5.3 Adapting for your repo](#53-adapting-for-your-repo)).
> [`schemas/hook_contract.md`](../../schemas/hook_contract.md) is the authoritative
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

A **single Python dispatcher** ([`hooks/workflow_hook.py`](../../hooks/workflow_hook.py))
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

### 2.4 Loop detection

The same handler watches for the agent retrying itself into a corner. Every tool
call is reduced to a signature —
`sha256(tool_name + "\0" + json.dumps(tool_input, sort_keys=True))`, first 16 hex
chars — and pushed onto a rolling 20‑entry window in the session state. When the
run of *consecutive identical* signatures reaches `loop_detection.repeat_threshold`
(default 3, clamped to a minimum of 2), the hook says so once and appends a line
to `loop_detection.log_path`:

```json
{"timestamp": "2026-08-04T21:57:10+08:00", "session_id": "…", "tool_name": "Bash",
 "signature": "be9fc650e7879079", "repeat_count": 3, "threshold": 3}
```

Judging on **arguments, not just the tool name** is the point: reading ten
different files is work, reading the same file ten times is a loop. Changing any
argument breaks the run. Each signature is announced at most once per session
(`loop_hits`), so a genuinely necessary retry loop doesn't turn into a nag.
`Stop` reports how many fired, pointing at `docs/RETROSPECTIVE.md`.

**Advisory only.** Like every other `PostToolUse` output, it cannot block — the
tool has already run. Set `loop_detection.enabled: false` to switch it off
entirely.

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

1. the working tree is **dirty on a branch other than the resolved main branch**
   (see §3.4) → commit & push
   (`git add -A && git commit -m "<msg>" && git push`; the reminder uses the `-m`
   form so an agent copying it can't hit a bare‑`git commit` editor hang or a
   stdin/heredoc rejection), and/or
2. `source_changed` **and not** `ledger_touched` → add a weekly‑ledger entry
   (`history/YYYY-Www.md`, What / Why / Refs).

If any reminder applies (and the caps allow), it increments `stop_block_count`,
saves state, and emits the block. Otherwise it exits `0` and the session ends.

### 3.4 Which branch counts as "main"

`resolve_main_branch()` decides which branch the dirty‑tree reminder treats as
home. Hard‑coding `main` nags every `master`/`trunk`/`develop` repo on every
close, so it resolves in precedence order:

| Order | Source | Cost |
|-------|--------|------|
| 1 | `stop_hook.main_branch`, if non‑empty — an explicit pin always wins | none |
| 2 | `git symbolic-ref --short refs/remotes/<remote>/HEAD` (unless `main_branch_autodetect` is `false`) | local ref read, **no network** |
| 3 | `git remote show <remote>` → `HEAD branch:` — only if `main_branch_probe_remote` is `true` | **network round‑trip** |
| 4 | `"main"` | none |

`<remote>` comes from `stop_hook.main_branch_remote` (default `origin`).
Resolution runs **after** the `stop_hook_active` / block‑cap short‑circuit, so a
suppressed `Stop` costs no git calls, and the answer is memoised in the session
state as `main_branch_detected` — one probe per session at most. Every step is
fail‑soft: a git failure just falls through to the next candidate.

The remote probe is opt‑in on purpose: `Stop` runs while the user is waiting for
the session to close, and a hanging network call there is far worse than an
occasional wrong branch guess. Step 2 covers the normal case, since `git clone`
writes `refs/remotes/origin/HEAD` for you (`git remote set-head origin --auto`
repopulates it if it is missing or stale).

---

## 4. State Persistence (Per‑Session)

State lives at:

```
{tempfile.gettempdir()}/workflow_hook_state_<sanitized_session_id>.json
```

**Fields**: see the state-key table in
[`schemas/hook_contract.md`](../../schemas/hook_contract.md), which is the authoritative
in-repo contract and the only place the key list is maintained. It is not restated here —
this document covers *integration* (settings wiring, deployment, platform behaviour); the
contract covers *I/O shapes and state*. Keeping one list in one file is what stops the two
from drifting apart.

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
[`.claude/settings.json`](../../.claude/settings.json):

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
runs, added alongside `hooks` in [`.claude/settings.json`](../../.claude/settings.json):

```json
{
  "permissions": {
    "allow": [
      "Read", "Grep", "Glob",
      "Bash(git status:*)", "Bash(git log:*)", "Bash(git diff:*)",
      "Bash(git fetch:*)", "Bash(git pull:*)", "Bash(git branch:*)",
      "Bash(git remote:*)", "Bash(git rev-parse:*)", "Bash(git show:*)",
      "Bash(python -m unittest:*)", "Bash(python --version)",
      "Bash(cat:*)", "Bash(ls:*)",
      "Bash(gh pr view:*)", "Bash(gh pr list:*)", "Bash(gh pr status:*)",
      "Bash(gh pr checks:*)", "Bash(gh repo view:*)"
    ]
  },
  "hooks": { "…": "…" }
}
```

- All entries are read‑only except `git fetch`/`git pull` — the workflow's
  sanctioned Phase‑0 sync (F1), safe to allow.
- Only **read‑only** `gh` subcommands are listed (`gh pr view/list/status/
  checks`, `gh repo view`). Do **not** allowlist writes like `gh pr merge`,
  `gh pr close`, or `gh pr create` — keep PR mutations gated. Note also that a
  *compound* command (`cd … && gh pr view … | head`) can still prompt even when
  `gh pr view:*` is allowed, because Claude Code evaluates the whole command
  line; run the allowlisted command on its own to avoid the prompt.
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
  "source_directories": ["hooks", ".claude/skills", "schemas", "templates"],
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
    "main_branch_autodetect": true,
    "main_branch_remote": "origin",
    "main_branch_probe_remote": false
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
| `stop_hook.main_branch` | The branch on which a dirty tree is *not* nagged (commits there are expected to be intentional). **Omit it** to let auto‑detection resolve it (§3.4); set it only to pin a branch detection would get wrong. |
| `stop_hook.main_branch_autodetect` | `true` (default) detects the default branch from `refs/remotes/<remote>/HEAD`; `false` restores the old "assume `main`" behaviour. Ignored when `main_branch` is pinned. |
| `stop_hook.main_branch_remote` | Remote whose `HEAD` detection consults (default `origin`; set e.g. `upstream` on a fork). |
| `stop_hook.main_branch_probe_remote` | `true` allows the `git remote show` fallback, which **contacts the remote**. Leave `false` unless your clones lack `origin/HEAD` and you accept a network call at session close. |
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

## 8. `--self-test` — config validation & governance health

Not a hook event. Run it by hand or in CI:

```bash
python hooks/workflow_hook.py --self-test
```

It is the **only** path in the dispatcher allowed to exit non‑zero, because a
human or a CI job invokes it — never Claude Code. It reads no stdin.

```text
Adaptive Workflow -- self-test
============================================================
config: /repo/.claude/workflow_config.json
root:   /repo

[ ok ] config valid against schemas/config_schema.json
[ ok ] weekly ledger history/2026-W32.md
[ ok ] plans/UNFINISHED.md absent
[ ok ] loop detection enabled
[ ok ] every doc carries frontmatter
[ ok ] tier-0 prohibitions: 4 defined
[ ok ] retrospective has entries

------------------------------------------------------------
Governance maturity: level 5/5 (Optimized)
```

**Validation** uses a stdlib subset of JSON Schema (`type`, `properties`,
`required`, `additionalProperties`, `enum`, `minimum`, `items`) so the repo keeps
its no‑dependency promise. The root config object is deliberately open
(`additionalProperties: true`) so a project can carry its own keys; nested blocks
are closed, so a typo inside one is a real error rather than an extension point.

**Exit code reflects validation only** — the maturity level is reported, never
enforced. A young repository sits at level 1–2 and still exits 0. Full check‑to‑level
mapping: [`schemas/hook_contract.md`](../../schemas/hook_contract.md).

On a console that can't encode the report (Windows `cp1252` and the API‑key
warning emoji), the output degrades to ASCII instead of crashing.

---

## Official References

- [Claude Code Hooks – Official Documentation](https://code.claude.com/docs/en/hooks)
- Authoritative in‑repo contract: [`schemas/hook_contract.md`](../../schemas/hook_contract.md)
- Behavioural spec: `GUIDE.md` §7

---

*End of Document – Implementation Guide v1.8*
