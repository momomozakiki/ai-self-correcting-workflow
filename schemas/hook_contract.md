# Hook I/O Contract

The dispatcher (`.claude/hooks/workflow_hook.py`) is invoked by Claude Code for four
hook events. For each, Claude writes a JSON event object to the hook's **stdin**
and reads a JSON object from its **stdout**. The hook **always exits 0**
(fail-soft): an error in the workflow tooling must never break a session.

Fail-soft has a consequence worth stating plainly, because `PreToolUse` is a
guard: a crash in a handler means the tool call is **allowed**. The dispatcher
fails open. Nothing here is a security boundary.

See `GUIDE.md` §7 for the full behavioural spec.

---

## Shared input fields

| Field | Type | Notes |
|-------|------|-------|
| `hookEventName` | string | `SessionStart` \| `PreToolUse` \| `PostToolUse` \| `Stop`. (`hook_event_name` is also accepted.) |
| `session_id` | string | Identifies the session; used to name the per-session state file. If absent, the hook runs statelessly. |

Per-session state lives at
`{tempdir}/workflow_hook_state_{sanitized_session_id}.json`. **This table is the
single source of truth for the state keys** — no other document restates it.

| Key | Type | Meaning |
|-----|------|---------|
| `source_changed` | bool | A file under `source_directories` was edited this session. |
| `ledger_touched` | bool | A file under `ledger.directory` was edited this session. |
| `doc_nudged` | bool | The one-time `PostToolUse` documentation advisory has fired. |
| `skill_nudged` | bool | The one-time `PostToolUse` skill-authoring advisory has fired (a file under `.claude/skills/` was edited). |
| `stop_block_count` | int | Number of `Stop` blocks emitted this session (capped by `stop_hook.max_blocks`). |
| `main_branch_detected` | str \| null | Auto-detected default branch, memoised on the first `Stop` so a session probes git at most once. |
| `recent_tool_calls` | list[str] | Rolling window (last 20) of tool-call signatures, for loop detection. |
| `loop_hits` | list[str] | Signatures already reported this session, so one loop is announced once. |
| `session_start_ts` | float | Creation timestamp, used for stale-state purging (>24h). |

Written atomically (temp sibling + `os.replace`). With no `session_id`, the hook
runs statelessly and none of the above persists.

---

## SessionStart

**Input:** `{ "hookEventName": "SessionStart", "session_id": "..." }`

**Behaviour:** purge stale state (>24h), reset session state, gather git
status, run `env_check` tool checks, parse the roadmap `**Next action:**`,
flag an unfinished plan, and — when `workflow_update_check.enabled` is true —
run the F5 daily update check.

**F5 update check (opt-in, default off):** no-op unless
`workflow_update_check.enabled`. When on, and the `submodule_path` (default
`.claude/workflow-core`) is a linked git repo, it is fetched at most once per
day (gated by the project-persistent `.ai/.workflow_check_date` file) and
compared against `{remote}/{branch}`. If the submodule is behind, a
`🔄 Workflow updates available (N new commits)` line is appended to the injected
context. **Detection & notification only — never auto-applies the update.**
Fail-soft: any git/network error leaves the check silent.

**`reloadSkills`:** emitted as `true` when `.claude/skills/` exists in the project,
omitted otherwise. Claude Code's live change detection does **not** watch a
top-level skills directory that did not exist when the session started, so a
skill added between sessions — or by the previous session — can sit on disk
unloaded, with no diagnostic. Asking for a re-scan at session start costs one
directory scan and removes that failure mode. It is gated on the directory
existing so the flag means something when it appears.

**Output:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "…markdown context injected into the session…",
    "sessionTitle": "Adaptive Workflow session",
    "reloadSkills": true
  }
}
```

---

## PreToolUse

**Matcher (in settings.json):** `Bash|PowerShell`. Both shells, because
`Bash(...)` and `PowerShell(...)` are separate permission namespaces — a
Bash-only guard is bypassed by the other tool.

**Input:**
```json
{
  "hookEventName": "PreToolUse",
  "session_id": "…",
  "tool_name": "Bash",
  "tool_input": { "command": "git push --force origin main" }
}
```

**Behaviour — the Tier-0 guard.** Splits the command on the separators the
permission matcher recognises (`&&`, `||`, `|&`, `;`, `|`, `&`, newline) and runs
four guards over each subcommand, so a prohibited call cannot hide behind a
benign one. Configured by `tier0_guard`; `enabled: false` disables it entirely.

| Guard | Decision | Fires on |
|-------|----------|----------|
| `guard_force_push` | `deny` | a force flag (`--force*`, `-f`, a `+refspec`) whose destination resolves to a protected branch |
| `guard_protected_paths` | `deny` | `rm` / `Remove-Item` / `git rm` targeting `tier0_guard.protected_paths` |
| `guard_history_rewrite` | `ask` | `git commit --amend`, `git rebase`, `git reset --hard`, `git filter-branch` |
| `guard_heredoc` | `ask` | heredoc / here-string, `-F -`, `--file=-`, `-F /dev/stdin`, bare `git commit` |

A `deny` anywhere outranks an `ask` anywhere. `ask` is used wherever the command
alone cannot settle the question — whether a commit is published, whether a
heredoc is the dangerous kind — so a false positive costs one keystroke rather
than blocking the session.

**State:** none. This handler runs before every shell call and deliberately
neither reads nor writes the session state file. Git is only consulted after a
force flag has already been parsed out of the command.

**Output — when a guard fires:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Tier-0 prohibition-force-push-shared: …"
  }
}
```

**Output — otherwise: nothing.** Silence defers to the normal permission flow.
Emitting `"allow"` would *approve* the call, auto-approving every shell command
in the session; the guard never does this.

**Known limits.** In `dontAsk` mode an `ask` becomes a silent block rather than a
prompt. Subcommand splitting does not honour quotes, so a separator inside a
quoted string can produce an extra fragment — over-reporting, which is the safe
direction. And the guard sees tool calls only, never a terminal opened outside
Claude Code; OS-level enforcement is the sandbox's job, not a hook's.

---

## PostToolUse

**Matcher (in settings.json):** `Edit|Write|MultiEdit`.

**Input:**
```json
{
  "hookEventName": "PostToolUse",
  "session_id": "...",
  "tool_name": "MultiEdit",
  "tool_input": {
    "file_path": "src/a.py",
    "edits": [ { "file_path": "src/b.py" } ]
  }
}
```
Both the top-level `file_path` and every `edits[].file_path` are collected.

**Behaviour:** set `source_changed` / `ledger_touched` flags by directory; emit
a one-time advisory nudge if source changed without a doc file being touched;
emit a one-time **skill advisory** when an edited path is under `.claude/skills/`
(`skill_nudged`); run loop detection (below). **Advisory only — never blocks.**

The skill advisory exists because skills fail silently in every direction: a
misplaced directory loads nothing, an unrecognised frontmatter key is ignored,
and a body past the compaction budget is truncated without a diagnostic. Nothing
reports any of it, so the moment just after a skill file is written is the only
cheap place to point at `skill-authoring`, `claude-code-layout`, the tests, and
the `templates/skills/` mirror. It cannot block — `PostToolUse` fires after the
write, so the file already exists by the time it runs.

**Loop detection** (`loop_detection.enabled`, default true). A signature is
`sha256(tool_name + "\0" + json.dumps(tool_input, sort_keys=True))`, truncated to
16 hex chars, so "the same call again" is judged on arguments, not just the tool.
Each call is appended to `recent_tool_calls`; the length of the run of identical
signatures ending at the current call is compared to `repeat_threshold` (default
3, **clamped to a minimum of 2** — a threshold of 1 would fire on every call).

On reaching the threshold, and only the **first** time for a given signature
(tracked in `loop_hits`), the hook appends one JSON line to `loop_detection.log_path`:

```json
{"timestamp": "2026-08-04T21:57:10+08:00", "session_id": "...", "tool_name": "Bash",
 "signature": "be9fc650e7879079", "repeat_count": 3, "threshold": 3}
```

Changing any argument breaks the run. Log writes are fail-soft: an unwritable path
silently skips the record and never affects the advisory.

**Output (only when nudging and/or reporting a loop; both are joined by a blank line):**
```json
{ "hookSpecificOutput": { "hookEventName": "PostToolUse", "additionalContext": "…" } }
```
Otherwise: no output.

---

## Stop

**Input:** `{ "hookEventName": "Stop", "session_id": "...", "stop_hook_active": false }`

**Behaviour:**
- If `stop_hook_active` is true **or** `stop_block_count >= stop_hook.max_blocks`
  → exit 0, no output (allow the session to end).
- Dirty working tree on a non-`main_branch` branch → commit reminder.
- `source_changed` && !`ledger_touched` → ledger reminder.
- `loop_hits` non-empty → a reminder naming how many loops fired, pointing at
  `docs/RETROSPECTIVE.md`.
- **Dirty working tree on _any_ branch → write a Phase-3 breadcrumb** to
  `plans/UNFINISHED.md` (see below). This happens whether or not the hook blocks.
- If any reminder: increment `stop_block_count`, emit a block decision.

**Detecting `source_changed` / `ledger_touched`.** The `PostToolUse` flags are the
fast path; a modification-time check against `session_start_ts` is the fallback.
`PostToolUse` only fires for `Edit|Write|MultiEdit`, so without the fallback a
ledger appended by a shell redirect reads as untouched (the reminder fires when
the work *was* done) and a source file rewritten by `sed -i` reads as unchanged
(the reminder never fires at all — the worse direction).

Still **not** `git diff HEAD`, which would count pre-session changes. Comparing
against `session_start_ts` keeps the reminder scoped to this session while being
blind to *how* a file was written. Configured by `stop_hook.mtime_fallback`,
`mtime_scan_limit` and `mtime_prune`. The source walk returns on the first file
newer than the threshold and gives up after the scan limit, so both the common
and worst cases are bounded — it runs at every `Stop`.

Two limits worth knowing:

- `git checkout` / `git pull` rewrite files and bump mtimes. A pull that touches
  the ledger can therefore suppress a legitimate reminder, and one that touches
  source can raise a spurious one.
- When the state file is missing, `load_state` returns a fresh `default_state()`
  whose `session_start_ts` is *now*, so every mtime reads as older and the
  reminder fires. That is the conservative direction.

The breadcrumb and the commit reminder use live `git status`.

**Main-branch resolution** (for the commit reminder), in precedence order:

1. A non-empty `stop_hook.main_branch` — an explicit pin always wins.
2. Auto-detection, unless `stop_hook.main_branch_autodetect` is false (default
   true): `git symbolic-ref --short refs/remotes/{main_branch_remote}/HEAD`
   (local ref, **no network**).
3. `git remote show {main_branch_remote}` → its `HEAD branch:` line — **only**
   when `stop_hook.main_branch_probe_remote` is true, because it contacts the
   remote. A `(unknown)` HEAD is ignored.
4. `main`.

Resolution happens **after** the `stop_hook_active` / block-cap short-circuit, so
a suppressed Stop makes no git calls, and the result is memoised in
`main_branch_detected` (persisted even when the hook does not block) so one
session probes at most once. Fail-soft: any git error falls through to the next
candidate.

**Phase-3 breadcrumb:** on a dirty tree the hook writes/refreshes
`plans/UNFINISHED.md` (timestamp, branch, `git status --porcelain` file list, and
the pending reminders) so the next `SessionStart` (F4) surfaces the unfinished
work — durable even if the reminder is ignored or the session is force-closed.
The file begins with the marker `<!-- workflow-hook: auto-breadcrumb -->`; the
hook overwrites only its own marked breadcrumb and **never** clobbers a
human-authored `UNFINISHED.md` (one lacking the marker). Fail-soft: write errors
never break session close.

**Output (only when blocking):**
```json
{ "decision": "block", "reason": "…what to do before ending…" }
```
Otherwise: no output.

---

## Flags

- `--dry-run` — compute and print output as normal but route state writes to a
  null session so nothing is persisted and no real block count increments.
- `--self-test` — see below.

---

## `--self-test`

The one path that reads no stdin and is **allowed to exit non-zero**, because a
human or CI invokes it, never a hook event.

```bash
python .claude/hooks/workflow_hook.py --self-test
```

**Behaviour**, in order:

1. Locate and parse `workflow_config.json`. Not found or unparseable → exit 1.
2. Validate it against `schemas/config_schema.json` using a stdlib subset
   validator (`type`, `properties`, `required`, `additionalProperties`, `enum`,
   `minimum`, `items`). No `jsonschema` dependency. Note the **root object sets
   `additionalProperties: true` deliberately**, so a project may carry its own
   keys; nested blocks are closed, so a typo inside one is a real error.
3. Run health checks: weekly ledger present, no stray `plans/UNFINISHED.md`,
   loop detection enabled, every doc under `documentation_directories` carries
   frontmatter (`*.prov.md` sidecars exempt — they *are* the provenance
   mechanism), tier-0 prohibitions present, retrospective has entries, and every
   `(recurring)` retrospective entry carries a `**Codified:**` line.
4. Warn if `ANTHROPIC_API_KEY` is set, and print the `env_check` tool versions.
5. Derive a cumulative maturity level and rewrite `governance.maturity_tracker`.

| Level | Name | Requires (cumulatively) |
|-------|------|--------------------------|
| 1 | Ad-hoc | config parses |
| 2 | Repeatable | config schema-valid; current ISO-week ledger exists |
| 3 | Defined | no `UNFINISHED.md`; loop detection on; all docs carry frontmatter |
| 4 | Managed | tier-0 prohibitions present; retrospective has entries |
| 5 | Optimized | no uncodified recurring mistakes |

**Exit code reflects validation only.** A young repository sits at level 1–2 and
still exits 0; the level is reported, never enforced.

**Output:** a plain-text report on stdout. If the console encoding cannot
represent it (Windows `cp1252` and the warning emoji), the report degrades to
ASCII rather than crashing or emitting mojibake.
