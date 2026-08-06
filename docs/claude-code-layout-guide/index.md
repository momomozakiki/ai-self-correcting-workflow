---
title: Claude Code — File, Folder Structure and Workflow (Golden Rule)
version: 6.1
last_validated: 2026-08-06
official: false
source: user-provided, origin unknown — compiled from https://code.claude.com/docs/en
tags: [claude-code, layout, hooks, skills, subagents, workflows, golden-rule]
applies_when: "Deciding where a skill, subagent, hook, rule, workflow or settings file must live, or how Claude Code's execution loop relates to this repository's own workflow."
estimated_tokens: 4200
---

# Claude Code — File, Folder Structure and Workflow

**Version 6.1** — *the project's designated golden rule for Claude Code layout, with verified errata.*

## Revision History

| Version | Date | Change |
|---------|------|--------|
| 6.0 | 2026-08-06 | Received as an external document; designated the project golden rule. |
| 6.1 | 2026-08-06 | Vendored with provenance. Added the Corrections section below after verifying the hook-event table against the live documentation and against this repository's running hook. |

---

## Provenance — read this before trusting any claim here

This document was **provided to the project, not authored by it**, and its origin is unknown.
It is designated the golden rule for layout decisions, so its status has to be stated exactly:

| | Date | What it means |
|---|---|---|
| The guide's own version line | 2026-08-06 | When the document says it was written |
| The docs it cites | **2026-07-16 → 2026-07-29** | The evidence behind it is up to three weeks older |
| This repository's verification | 2026-08-06, against **v2.1.223** | When its claims were last checked against live docs |
| Runtime in use | **v2.1.223** | What actually runs here |

`official: false` is deliberate. The guide reads as authoritative and cites official URLs, but
it is a third-party compilation, and Corrections below shows it diverges from the pages it
cites. **Where this document and <https://code.claude.com/docs/en> disagree, the live docs
win** — and where the running system disagrees with both, the running system wins.

---

## Corrections (verified 2026-08-06 against live docs and running code)

Three errors, each checked rather than argued. They are recorded here rather than silently
patched into the body so that a reader comparing this copy against the original can see
precisely what changed and why.

### 1. The hook-event blocking table is wrong

The guide's Part 5.3 marks a set of events "Can Block? No". The live
[hooks reference](https://code.claude.com/docs/en/hooks), under *Exit code 2 behavior per
event*, says otherwise:

| Event | Guide v6.0 | Live docs (verbatim) |
|---|---|---|
| `Stop` | No | **Yes** — "Prevents Claude from stopping, continues the conversation" |
| `SubagentStop` | No | **Yes** — "Prevents the subagent from stopping" |
| `PreCompact` | absent | **Yes** — "Blocks compaction" |
| `PostToolBatch` | No | **Yes** — "Stops the agentic loop before the next model call" |

Also blocking per the live docs, and marked non-blocking or absent in the guide:
`UserPromptSubmit`, `PermissionRequest`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`,
`ConfigChange`, `WorktreeCreate`, `Elicitation`, `ElicitationResult`.

**This one is falsifiable against running code, and was falsified.** This repository's
`Stop` hook emits `{"decision": "block", "reason": …}` from
`.claude/hooks/workflow_hook.py::handle_stop`, and on 2026-08-06 that block **fired in a live
turn**: the session did not end, the reason surfaced, and the turn resumed. Documentation,
implementation and observed behaviour all agree the guide is wrong here.

### 2. The event list is incomplete, and internally inconsistent

The guide's table lists **24** events. The live docs list **31**. Missing: `DirectoryAdded`,
`WorktreeRemove`, `PreCompact`, `PostCompact`, `Elicitation`, `ElicitationResult`,
`SessionEnd`.

Separately, the guide's own v6.0 changelog claims it "added `PreCompact` and `PostCompact` to
hook events" — neither appears in its table. That inconsistency is visible without consulting
any external source.

The authoritative list in this repository is `tests/test_claude_layout.py::HOOK_EVENTS`, which
carries all 31 and fails the build on an unknown event name in any settings file.

### 3. Exit-code semantics are misstated

The guide says exit 1 means "show error to user but continue" and that exit 2 blocks
"(PreToolUse only)". Per the live docs: exit 2 is the **general cross-event** blocking path,
with per-event effects; and exit 1 is a **non-blocking error** — the docs call this out
explicitly because 1 is the conventional Unix failure code and does *not* block here.

### What was not changed

The guide's core distinction — **discovered by location vs registered elsewhere** — is correct
and is confirmed by the live docs. In particular its statement that **there is no
`.claude/hooks/` discovery mechanism** is right: the directory does not appear in the official
`.claude` tree, and hook scripts run only because `settings.json` names them. This repository
nonetheless keeps its dispatcher at `.claude/hooks/workflow_hook.py`, as an organisational
convention, not because the location makes it load.

---

## How to re-verify this document

Do not trust the dates above on sight; they go stale silently. The procedure lives in
`.claude/skills/skill-authoring/SKILL.md` and is, in short:

1. Read the installed version — `ls ~/.vscode/extensions/anthropic.claude-code-*`, taking the
   **highest**, not the first. Several coexist; this document's earlier draft recorded v2.1.221
   because it read the first of two.
2. Diff the [release notes](https://github.com/anthropics/claude-code/releases) from the stamped
   version to that one.
3. Re-read each cited doc page — the whole page, not the section you remember.
4. Confirm or correct every claim, then update `last_validated` and the version stamp.
5. Log the re-verification in the weekly ledger.

**A reference page is not the whole record.** Version floors live in the release notes, and
"not documented on the page I read" is not "not documented" — this repository has made that
mistake twice, recorded in `skill-authoring/references/verified-facts.md` and in
`claude-code-layout/references/frontmatter-by-type.md`.

---

## The guide itself

The operational content of this guide is maintained as a skill rather than duplicated here, so
that there is one copy to keep current rather than two that drift:

- **[claude-code-layout](../../.claude/skills/claude-code-layout/SKILL.md)** — the
  discovered-vs-registered distinction, the two precedence orders, the full directory map, and
  what to check when a piece of configuration has no effect.
- **[references/directory-map.md](../../.claude/skills/claude-code-layout/references/directory-map.md)**
  — every path, what reads it, and how it fails when misplaced.
- **[references/frontmatter-by-type.md](../../.claude/skills/claude-code-layout/references/frontmatter-by-type.md)**
  — skills vs subagents vs commands, including the near-miss field names.
- **[skill-authoring](../../.claude/skills/skill-authoring/SKILL.md)** — structuring, sizing
  and splitting a skill.

The skill is the operative artifact: it is what Claude Code loads, and
`tests/test_claude_layout.py` and `tests/test_skills.py` hold it to the layout it describes.
This document is the golden-rule *reference* and the record of where the received guide was
wrong.

### Material this guide contributed

Folded into the skill rather than kept here:

- `.worktreeinclude` at the repository root — gitignored files copied into new worktrees.
- The managed-policy `CLAUDE.md` location in the memory hierarchy
  (`/etc/claude-code/CLAUDE.md` on Linux/WSL; the macOS and Windows paths differ — see
  `/docs/en/memory`).
- The five hook types: `command`, `prompt`, `agent`, `http`, `mcp_tool`.
- The orchestrator distinction (its Part 10): with subagents, skills and agent teams **Claude**
  is the orchestrator and every result lands in a context window; with a dynamic workflow the
  **script** holds the loop and Claude's context holds only the final answer.
- `ultracode`, which sets effort to `xhigh` and lets Claude decide when to use a workflow.

---

## Relationship to this repository's own workflow

Worth stating, because the question "should we use the Claude workflow instead?" has a
misleading shape. They are **different layers, not alternatives**:

| | Claude Code's loop | Adaptive Self-Correcting Workflow |
|---|---|---|
| What it is | The runtime: Think → Act → Observe, with hooks firing at fixed lifecycle points | Process governance: ledger, provenance, planning, closure |
| Who implements it | Claude Code | This repository |
| How they meet | — | The workflow rides *on* the loop, through `PreToolUse`, `PostToolUse`, `SessionStart` and `Stop` |

The guide describes no process that could replace Phase 0–3, and Phase 0–3 cannot replace the
execution loop. The real question the guide raises is narrower and worth acting on: the
dispatcher implements **4 of 31** available events. That assessment is
`docs/hook-event-assessment.md`.
