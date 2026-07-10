# Hook I/O Contract

The dispatcher (`hooks/workflow_hook.py`) is invoked by Claude Code for three
hook events. For each, Claude writes a JSON event object to the hook's **stdin**
and reads a JSON object from its **stdout**. The hook **always exits 0**
(fail-soft): an error in the workflow tooling must never break a session.

See `GUIDE.md` §7 for the full behavioural spec.

---

## Shared input fields

| Field | Type | Notes |
|-------|------|-------|
| `hookEventName` | string | `SessionStart` \| `PostToolUse` \| `Stop`. (`hook_event_name` is also accepted.) |
| `session_id` | string | Identifies the session; used to name the per-session state file. If absent, the hook runs statelessly. |

Per-session state lives at
`{tempdir}/workflow_hook_state_{sanitized_session_id}.json` and holds
`source_changed`, `ledger_touched`, `stop_block_count`, `doc_nudged`,
`session_start_ts`.

---

## SessionStart

**Input:** `{ "hookEventName": "SessionStart", "session_id": "..." }`

**Behaviour:** purge stale state (>24h), reset session state, gather git
status, run `env_check` tool checks, parse the roadmap `**Next action:**`,
flag an unfinished plan.

**Output:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "…markdown context injected into the session…",
    "sessionTitle": "Adaptive Workflow session"
  }
}
```

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
a one-time advisory nudge if source changed without a doc file being touched.
**Advisory only — never blocks.**

**Output (only when nudging):**
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
- If any reminder: increment `stop_block_count`, emit a block decision.

Detection uses the **session state file**, not `git diff HEAD` (which would
include pre-session changes).

**Output (only when blocking):**
```json
{ "decision": "block", "reason": "…what to do before ending…" }
```
Otherwise: no output.

---

## Flags

- `--dry-run` — compute and print output as normal but route state writes to a
  null session so nothing is persisted and no real block count increments.
