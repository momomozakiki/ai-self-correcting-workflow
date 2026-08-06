---
paths:
  - ".claude/**"
  - "templates/skills/**"
  - "templates/settings.json.hooks"
---

# Claude Code configuration layout

Verified 2026-08-06 against Claude Code v2.1.223.

This rule is **path-scoped**: it loads when you touch configuration, and not otherwise. That is
deliberate, and so is what is *not* here — a path-scoped rule is not re-injected after
`/compact` until a matching file is read again, so nothing unconditional belongs in it. Tier 0
prohibitions and the direct-test guard live in `CLAUDE.md`, ungated, for exactly that reason.

The full treatment is the `claude-code-layout` skill. This is the part worth having in context
the moment you open a file under `.claude/`.

## Discovered or registered — get this backwards and nothing works

| | Wiring | Failure |
|---|---|---|
| **Discovered by location** — `skills/`, `agents/`, `commands/`, `output-styles/`, `rules/`, `workflows/` | The directory and filename *are* the wiring | Elsewhere it is inert: no command, no error, every frontmatter field dead |
| **Registered elsewhere** — hook scripts | A `settings.json` entry names the script | Miss the registration and the code is unreachable |

**There is no `.claude/hooks/` discovery.** This repository keeps its dispatcher there as an
organisational convention; it runs because `.claude/settings.json` names it, not because of
where it sits. Moving a hook script is safe. Moving a skill is not.

## Before adding or moving anything

1. Decide which of the two it is.
2. If discovered — exact path, exact filename case.
3. If registered — does the registration exist in **every** settings file that ships? Here that
   means `.claude/settings.json` *and* `templates/settings.json.hooks`. They drifted once, and
   every adopter ran without a Tier-0 guard while the suite stayed green.
4. **Prove it loads.** Not "the file is correct" — observe it: the skill appears in the
   listing, the guard returns its `deny`, the hook's context shows up.
5. `python -m unittest tests.test_claude_layout tests.test_skills`.

## Mirrors

`.claude/skills/` → `templates/skills/`, `.claude/rules/` → `templates/rules/`, and
`.claude/agents/` → `templates/agents/`, each in the same commit. Adopters copy from
`templates/`; the parity tests fail otherwise.

## Frontmatter near-misses

Skills use `disallowed-tools` (hyphenated). Subagents use `disallowedTools` (camelCase). An
unrecognised key is ignored in silence. Subagent identity comes from the `name` field, not the
filename, and as of v2.1.218 a name containing `:` means the file is not loaded at all — the
error goes only to the debug log.
