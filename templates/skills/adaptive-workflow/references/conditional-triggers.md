# Conditional triggers and the ledger

Apply these during and after each change in Phase 2. A trigger that fires and is not acted on
is the most common way an otherwise correct change goes unrecorded.

| Trigger | Action |
|---------|--------|
| New pattern / rule / gotcha | Append to `.ai/best_practices.md` (with example). |
| New naming convention | Append to `.ai/naming_conventions.md`. |
| Change to public API / architecture / data flow | Update `docs/*.md` (dated). |
| Doc created / updated | Apply the Documentation Standard: frontmatter (provenance + version) + `last_validated` refresh + a Revision History row; fold into a folder per GUIDE §6.4 if it outgrows one question / its token budget, or its Revision History passes ~8 rows (relocate history to a sibling `CHANGELOG.md`). See [doc-frontmatter.md](doc-frontmatter.md). |
| Non-obvious technical decision | Decision log in `plans/archive/<slug>/execution_log.md`. |
| New significant directory with a distinct responsibility (large/monorepo projects) | Optionally add a `SCOPE.md` describing its role + DO/DON'T rules; link it from the parent's `SCOPE.md` (Progressive Disclosure Guide §3.1). Skip for small projects. |
| Repeatable mistake | Warning in best practices / retro note. |
| **Any intentional change** (not a trivial typo/whitespace edit) | **Append a ledger entry** to `history/YYYY-Www.md`. Add an optional `**Risk:**` line using one of `privilege \| design \| behavioral \| structural \| accountability` when the change carries real risk — omit it when it doesn't, or the field stops meaning anything. |
| Mistake worth remembering | Entry in `docs/RETROSPECTIVE.md`. If it's already there, append `(recurring)` to the heading — it now owes a rule file under `.ai/01-phases/` and a line in `SKILL.md`. |
| New rule harvested from a real mistake | Add the rule file, update the folder's `manifest.json` in the same edit, mirror it into `templates/ai-library/`, and set `enforcement_status` honestly: `live` needs an `enforced_by` list naming real code, `convention` needs an `enforcement_note` saying what the real mechanism is. `tests/test_governance_library.py` checks all of it. See `.ai/GROWTH.md`. |
| New or restructured skill | Follow the [`skill-authoring`](../../skill-authoring/SKILL.md) skill, and mirror `.claude/skills/` into `templates/skills/` in the same commit. `tests/test_skills.py` checks both, and a one-time `PostToolUse` advisory fires on the first edit under `.claude/skills/`. |
| Any Claude Code configuration added or moved (skill, subagent, command, rule, workflow, hook, settings) | Follow [`claude-code-layout`](../../claude-code-layout/SKILL.md): confirm whether it is *discovered by location* or *registered elsewhere*, and prove it loads rather than assuming. `tests/test_claude_layout.py` enforces the placement rules. |
| External doc without provenance | Ask for the official URL, then add the doc frontmatter (provenance fields). |
| Completed task affects roadmap | Update the roadmap. |
| Epic finished | Move it to `## Completed Epics`. |

## Ledger (mandatory)

Log every qualifying change in `history/YYYY-Www.md` (create the file on the first change of
the week).

- **Substantial** change → full `What / Why / Refs`.
- **Trivial or routine** → a one-line note.
- **Tags:** `[design] [doc] [code] [workflow] [config] [decision] [data]`.
- Reference the commit SHA and/or the plan slug.

Write the entry when you make the change, not from memory at the end of the session. The
entry written later is the one that omits the reason.

`history/FORMAT.md` holds the full format.
