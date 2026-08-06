<!-- workflow-hook: auto-breadcrumb -->
# Unfinished session — auto-recorded 2026-08-06 19:09:42

> This breadcrumb was written by the workflow Stop hook because the
> working tree was dirty at session end (Phase 3 not completed).
> Review, finish closure, then delete this file. It will be
> overwritten by the hook while it remains a breadcrumb, but a
> human-authored plan placed here is never overwritten.

**Branch:** `feat/governance-v14-integration`

**Pending closure steps:**
- Working tree is dirty on branch `feat/governance-v14-integration`. Phase 3 closure: commit & push before ending (`git add -A && git commit -m "<msg>" && git push`; avoid a bare `git commit`, which can open an editor and hang, and avoid heredocs / `-F -`).
- Source files changed this session but the weekly ledger (history/YYYY-Www.md) wasn't updated. Add an entry (What / Why / Refs) before closing.

**Uncommitted files (`git status --porcelain`):**

```
  M .ai/01-phases/manifest.json
   M .claude/skills/adaptive-workflow/SKILL.md
   M templates/ai-library/01-phases/manifest.json
   M templates/skills/adaptive-workflow/SKILL.md
  ?? .ai/01-phases/rule-direct-test-disputes.json
  ?? templates/ai-library/01-phases/rule-direct-test-disputes.json
```
