---
title: Retrospective — mistakes, root causes, and what they became
version: 1.0
last_validated: 2026-08-04
official: true
source: agent-generated
tags: [retrospective, self-hardening, mistakes, governance]
applies_when: "Closing a task (Phase 3), or checking whether a mistake has happened before."
estimated_tokens: 900
---

# Retrospective
**Version 1.0** — *The self-hardening loop's input. A mistake recorded twice becomes structure.*

## Revision History
| Version | Date       | Change   |
|---------|------------|----------|
| 1.0     | 2026-08-04 | Initial, seeded with two real mistakes from the v14 integration session. |

---

## How to use this file

Log a mistake when it costs time or produces a wrong result — not every stumble. One `###`
heading per mistake.

- **First occurrence**: write it up. That's all.
- **Second occurrence**: append `(recurring)` to the heading. It now owes a rule.
- **Codified**: once the rule exists, add a `**Codified:**` line naming it.

`python hooks/workflow_hook.py --self-test` reports any `(recurring)` entry that still has
no `**Codified:**` line, and withholds maturity level 5 until none are outstanding. The
threshold is deliberately two: one mistake is noise, two is a pattern worth paying for.

---

### 2026-08-04 — Heredoc-fed stdin mangles escape sequences (recurring)

- **What:** Patching `hooks/workflow_hook.py` via `python - <<'PY' ... PY` corrupted the
  script: `\\n` inside the Python source arrived as a real newline, so every replacement
  pattern containing an escape failed to match.
- **Why it matters:** The failure is silent until a pattern misses. Worse, a partial match
  would have written a half-patched file.
- **Root cause:** Feeding a program to an interpreter over heredoc stdin puts the shell
  between you and your source. Quoting the delimiter (`<<'PY'`) suppresses *variable*
  expansion but is not a guarantee across shells and tool layers.
- **Why this is recurring:** The same root cause was already documented once, for
  `git commit -F -` and heredoc commit messages (GUIDE §4 Phase 3, v4.6). This is the second
  manifestation, so the guidance is generalised rather than left as a git-specific caveat.
- **Fix:** Write the script to a file and run the file. For edits to tracked source, prefer
  the editing tools over generated patch scripts entirely.
- **Codified:** `.ai/01-phases/rule-no-heredoc-stdin.json`; GUIDE §4 Phase 2; SKILL.md Phase 2.

### 2026-08-04 — An environment check that could never pass

- **What:** Added `claude` to `env_check.tool_paths` so `SessionStart` would report the CLI
  version (the `opus` alias needs v2.1.219+). The CLI isn't on `PATH` in this environment —
  Claude Code runs as a VS Code extension — so every session would have reported
  `claude: NOT FOUND`.
- **Why it matters:** A check that always fails trains the reader to ignore the whole block.
  A false negative is worse than no check, because it costs attention on every session and
  eventually devalues the true negatives sitting next to it.
- **Root cause:** Adding the check without first verifying the probe could succeed here.
- **Fix:** Removed the entry. The version guidance is printed unconditionally as a note in
  `--self-test`, where it is accurate without pretending to have measured anything.
- **Codified:** not yet — first occurrence. If a second unverifiable check appears, this
  becomes a rule: *never add a health check without observing it pass and fail.*
