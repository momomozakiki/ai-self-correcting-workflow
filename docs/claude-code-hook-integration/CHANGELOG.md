---
title: Claude Code Hook Integration — full revision history
version: 1.0
last_validated: 2026-08-04
official: false
source: agent-generated
exclude_from_ai: true
tags: [changelog, history, excluded]
applies_when: "Never load — relocated history for the hook integration guide. See index.md for current truth."
estimated_tokens: 400
---

# Claude Code Hook Integration — Changelog

Relocated per GUIDE §6.3/§6.4 when the in-file table passed ~8 rows. A **sibling
peer** of `index.md`, not a split child: no `parent:` link, not in the child index,
and `exclude_from_ai: true` so retrieval skips it before scoring.

> **Moved 2026-08-04:** this guide was previously the flat file
> `docs/claude-code-hook-integration.md`. Historical revision rows in `GUIDE.md` and
> the repo `CHANGELOG.md` still name the old path — they describe what was true when
> written and are deliberately not rewritten.

| Version | Date       | Change |
|---------|------------|--------|
| 1.13    | 2026-08-04 | Loop detection (§2.4) and `--self-test` (§8) documented. §4 state-field list replaced by a pointer to `schemas/hook_contract.md`, which is now the single maintained list. Folded into a folder; history relocated here. |
| 1.12    | 2026-08-04 | New §3.4: `main_branch` resolution order (explicit pin → local `refs/remotes/<remote>/HEAD` → opt-in `git remote show` → `main`). Adds the three `stop_hook.main_branch_*` keys to §5.2/§5.3 and `main_branch_detected` to §4. |
| 1.11    | 2026-07-18 | §3.2 Stop-reminder mirror: use the `git commit -m "<msg>"` form so an agent copying it can't hit a bare-`git commit` editor hang or a stdin/heredoc rejection. |
| 1.10    | 2026-07-18 | §5.1.1: added read-only `gh` commands to the allowlist example and a note that writes (`gh pr merge`) stay gated and compound commands can still prompt. |
| 1.9     | 2026-07-18 | Added §5.1.1 documenting the `permissions.allow` allowlist that stops plan mode from prompting on every read-only `Bash` command. |
| 1.8     | 2026-07-10 | Migrated to the unified Documentation Standard: SOURCE-PROVENANCE comment → YAML frontmatter; changelog moved from the comment's `Notes:` field into this table. |
| 1.7     | 2026-07-10 | Realigned the guide with the real Python dispatcher and this repo's actual `.claude/workflow_config.json`; established as the golden reference for adopters. |
| 1.6     | (prior)    | Described a different (Flutter/Dart) project — superseded. |
| ≤ 1.3   | (prior)    | Described a hypothetical Node.js design — superseded. |
