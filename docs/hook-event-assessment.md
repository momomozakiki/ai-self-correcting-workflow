---
title: Hook Event Assessment — which of the 31 events this workflow should use
version: 1.0
last_validated: 2026-08-06
official: false
source: agent-generated
tags: [hooks, workflow, roadmap, assessment]
applies_when: "Deciding whether to wire an additional Claude Code hook event into the dispatcher."
estimated_tokens: 2600
---

# Hook Event Assessment

**Version 1.0** — *which of Claude Code's 31 hook events this workflow should use, and why the other 27 stay unwired.*

## Revision History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-08-06 | Initial assessment. Recommendations only — nothing wired in this pass. |

Verified 2026-08-06 against Claude Code v2.1.223, from
<https://code.claude.com/docs/en/hooks>.

---

## Where things stand

`.claude/hooks/workflow_hook.py` handles **4 of 31** events: `SessionStart`, `PreToolUse`,
`PostToolUse`, `Stop`. That ratio is not itself a problem — most of the 31 are irrelevant to a
process-governance workflow. This assessment exists so that "we only use four" is a decision
with reasons attached rather than an accident nobody revisited.

**Two constraints shape every recommendation below.**

*The dispatcher fails open.* Every handler is wrapped so the process exits 0 (GUIDE §7.5). An
exception means the action proceeds. Any new event inherits that, so an event whose value
depends on reliably stopping something is a poor fit.

*Advisory beats blocking.* The three events that could block and don't (`PostToolUse` can't;
`PreToolUse` and `Stop` do, narrowly) reflect a deliberate posture: nudge, don't wall. A
blocking hook that misfires trains people to route around the whole system.

---

## Recommended

### `PreCompact` — make the breadcrumb survive compaction

**The gap.** `plans/UNFINISHED.md` is written by the `Stop` hook on a dirty tree. But a long
session compacts *before* it stops, and per `/docs/en/memory` a compaction drops nested
CLAUDE.md files and path-scoped rules until something re-triggers them. The in-flight plan
state is exactly what a compaction is most likely to lose, and `Stop` fires too late to help.

**What it would do.** Write the same breadcrumb `write_unfinished_breadcrumb()` already writes,
on the same dirty-tree condition. No new logic — a second trigger for existing behaviour.

**Cost.** Low. The function is idempotent and refuses to overwrite a human-authored file, both
already tested.

**What must be true to adopt:** confirm `PreCompact` fires before context is discarded, not
after — the docs say it can block compaction, which implies "before", but that should be
observed rather than inferred. **Recommended.**

### `SessionEnd` — the closure check that currently never runs

**The gap.** Phase 3 says the work is not done until `UNFINISHED.md` is cleared, the ledger is
written, and the commit is pushed. Nothing checks that at the point it stops being fixable.
`Stop` fires per *turn*, not per session, and is capped at `max_blocks: 2` — so on a long
session the reminder is spent early and silence at the end means nothing.

**What it would do.** One non-blocking summary at session end: dirty tree, unwritten ledger,
unpushed commits, breadcrumb still present.

**Cost.** Low; `SessionEnd` cannot block, so it is advisory by construction.

**What must be true to adopt:** that `SessionEnd` fires reliably on an abrupt exit — the case
that matters most is precisely the one where the user closes the terminal. If it only fires on
a graceful quit, the value drops sharply. **Recommended, subject to that.**

---

## Worth considering

### `SubagentStop` / `TaskCompleted` — work the `Stop` hook cannot see

Subagents run in their own context and return only a summary. If one edits source files, the
`source_changed` flag is set by `PostToolUse` in the *main* session only if the main session
did the writing. Delegated work can therefore land unlogged, and the ledger reminder never
fires because nothing observed the change.

**Cost.** Moderate: per-session state is keyed by `session_id`, and it needs verifying whether
a subagent shares the parent's id or carries its own. That determines whether this is a flag
update or a state-merging problem.

**Verdict:** worth doing *after* `PreCompact` and `SessionEnd`, and only once the id question
is answered by observation.

### `PermissionDenied` — observability for guard hits

Every Tier-0 `deny` is currently invisible after the fact. The loop detector already writes
`.ai/08-behavioral-metrics/loop_detection.jsonl`; guard hits could use the same channel, making
"how often does the guard actually fire?" answerable instead of anecdotal.

**Cost.** Low. **Verdict:** nice-to-have. Genuine value, no urgency.

---

## Not recommended

### `UserPromptSubmit`

It **can block** (contrary to the vendored guide's table). That is the reason to avoid it: a
fail-open dispatcher gaining a path that can reject the user's prompt is a bad trade. A crash
in that handler is harmless by design, but a *false positive* silently eats input. There is no
Phase 0–3 obligation that needs enforcing before the prompt is read.

### `FileChanged`

Already reasoned in GUIDE §7.3 and unchanged: its matcher takes literal filenames, and the
ledger filename rolls over weekly (`history/YYYY-Www.md`). A matcher pinned to this week's file
silently stops matching next Monday — the exact silent-staleness failure this repo keeps
finding. `PostToolUse` on `Edit|Write|MultiEdit` covers the need without a date-dependent
matcher.

### `PostToolBatch`, `TeammateIdle`, `WorktreeCreate`, `Elicitation`, `ElicitationResult`, `ConfigChange`, `CwdChanged`, `DirectoryAdded`, `WorktreeRemove`, `Notification`, `MessageDisplay`, `StopFailure`, `PostToolUseFailure`, `Setup`, `InstructionsLoaded`, `PermissionRequest`, `SubagentStart`, `TaskCreated`, `PostCompact`

No Phase 0–3 obligation attaches to any of them. `InstructionsLoaded` is the closest to useful —
it can log which instruction files actually loaded, which would have caught the repo-root
`skills/` defect — but `tests/test_claude_layout.py` now catches that class statically, at
build time rather than per session, which is strictly better.

---

## Summary

| Event | Verdict | Blocker to adoption |
|---|---|---|
| `PreCompact` | **Recommended** | Confirm it fires before context is discarded |
| `SessionEnd` | **Recommended** | Confirm it fires on abrupt exit, not only graceful quit |
| `SubagentStop` / `TaskCompleted` | Worth considering | Does a subagent share the parent `session_id`? |
| `PermissionDenied` | Nice-to-have | None |
| `UserPromptSubmit` | No | Blocking path in a fail-open dispatcher |
| `FileChanged` | No | Literal matcher vs weekly-rolling ledger filename |
| The remaining 19 | No | No workflow obligation attaches |

Both "must be true" conditions are **observations, not inferences** — per
`.ai/01-phases/rule-direct-test-disputes.json`, wire nothing on the strength of a docs reading
alone. Accepted items go to `ROADMAP.md`; **nothing is wired by this document.**
