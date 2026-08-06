# Verified facts about Claude Code skills

Verified 2026-08-06 against Claude Code v2.1.223 — every claim below. Re-verify
before trusting any of it in a later version; several carry explicit version floors, which is
evidence the surface moves.

**Name the source, not just the fact.** There are three, and they do not say the same things:

| Source | Carries |
|---|---|
| <https://code.claude.com/docs/en/skills> | Behaviour and the frontmatter field list |
| <https://code.claude.com/docs/en/hooks> | Hook output shapes, including `reloadSkills` |
| <https://github.com/anthropics/claude-code/releases> | **Version floors and new commands** |

This matters because it has already caused one wrong entry here. The `disallowed-tools` floor
below was recorded as "no documented minimum" on the reasoning that the docs page annotates
twelve version floors and gives none for that field. The reasoning was sound and the conclusion
was wrong: the floor is in the release notes. **A reference page is not the whole record** —
"not documented on the page I read" is not "not documented". Check the release notes before
recording an absence.

## Discovery and precedence

| Location | Path |
|---|---|
| Enterprise | managed settings paths |
| Personal | `~/.claude/skills/<name>/SKILL.md` |
| Project | `.claude/skills/<name>/SKILL.md` |
| Plugin | `<plugin>/skills/<name>/SKILL.md` |

Precedence on a name collision: **enterprise overrides personal, personal overrides project**.
Any of these overrides a bundled skill of the same name. Plugin skills are namespaced
`plugin-name:skill-name` and cannot collide.

**No other location is discovered.** There is no settings key and no manifest field that
registers an alternative skills root. A repo-root `skills/` directory is invisible — this
repository shipped that defect and every frontmatter field in those files was inert until
2026-08-06. See `docs/RETROSPECTIVE.md`.

Nested `.claude/skills/` below the working directory **are** discovered, but not at startup:
they load the first time Claude reads or edits a file in that subdirectory, and appear under a
directory-qualified name such as `/apps/web:deploy`. Project skills also load from every
parent directory up to the repository root.

A `<skill-name>` entry may be a **symlink** to a directory elsewhere; Claude Code follows it
and loads the skill once even if reachable from several locations.

`--add-dir` / `/add-dir` load `.claude/skills/` from the added directory — an explicit
exception to the rule that additional directories grant file access, not configuration. The
`permissions.additionalDirectories` setting does **not** do this.

Skills beat commands: a skill and a `.claude/commands/` file with the same name resolve to the
skill. Custom commands have been merged into skills; `.claude/commands/` files keep working
and support the same frontmatter.

## Live change detection, and how to force a reload

Claude Code watches skill directories and picks up added, edited or removed skills within the
session, with no restart. **Exception:** a top-level skills directory that did not exist when
the session started is not watched.

**`/reload-skills` re-scans the skill directories without restarting the session** — added in
v2.1.152 alongside `disallowed-tools`. Reach for it first; a restart discards the whole
conversation, and the reload does not. A `SessionStart` hook can trigger the same thing by
returning `hookSpecificOutput.reloadSkills: true` (hooks reference).

The skills docs page still says to restart and mentions neither. That is the gap this file's
source table exists to close.

## Content lifecycle and budgets

- An invoked skill's rendered content enters the conversation **once and stays** for the rest
  of the session. Claude Code does **not** re-read the file on later turns. Write standing
  instructions, not one-time steps.
- Re-invoking a skill whose rendered content is unchanged adds a short "already loaded" note
  rather than a second copy (v2.1.202+).
- **After auto-compaction, only the first 5,000 tokens of each skill are re-attached**, and
  all re-attached skills share a **25,000-token combined budget**, filled from the most
  recently invoked backwards. Older skills can be dropped entirely.
- Descriptions are always in context; bodies are not. `description` + `when_to_use` are
  truncated at **1,536 characters** in the listing.
- Documented body recommendation: **keep `SKILL.md` under 500 lines**, moving detail to
  separate files.

Consequence: the 5,000-token re-attach cut-off is a tighter constraint than the 500-line
recommendation for dense prose, and it fails silently.

## Supporting files

The Claude Code docs show supporting files as flat siblings (`reference.md`, `examples.md`)
plus a `scripts/` directory; the Anthropic authoring best practices use `references/`,
`scripts/` and `assets/`. Both work — nothing parses these names. This repository standardises
on `references/`, `scripts/`, `assets/`.

Guidance is to keep file references **one level deep** from `SKILL.md` and avoid deeply nested
reference chains. That is a legibility rule, not an enforced mechanism.

## Corrections to the supplied "Definitive Guide" v3.0

| Guide claim | Verified reality |
|---|---|
| `name` cannot contain "anthropic" or "claude" | Not stated in the Claude Code docs. Unverified — do not assert it. |
| `description` max 1,024 characters | The open standard says 1,024; Claude Code truncates `description` + `when_to_use` at 1,536 in the listing. |
| A validator rejects the Claude Code extension fields | Unverifiable — no such validator is documented. The field list quoted in the guide also spells it `user-invokable`, which contradicts the documented `user-invocable`. |
| `@path` imports work in `SKILL.md` | Not documented anywhere. Do not use. |
| Deep nesting causes "partial reads" | Not a documented behaviour; it is style guidance. |
| Field table | Omits `when_to_use`, `arguments`, `disallowed-tools`, `effort`, `background`, `paths`, `shell`. |
| Substitution table | Omits `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_EFFORT}`. |
| Skill beats a same-named command is "observed behavior" | It is documented, not merely observed. |
| `background` is "background information for the skill" (v4.0) | Wrong. It applies **only** with `context: fork`; `false` waits for the subagent's result in the invoking turn instead of backgrounding it; default `true`; requires v2.1.218+. |
| `version` is a frontmatter field (v4.0) | Not in the documented field list. `tests/test_skills.py` rejects it, which is correct — an unrecognised key is ignored silently at runtime. |
| `shell` dropped from the field table (v4.0) | It is real: `bash` (default) or `powershell`, selecting the shell for `` !`cmd` `` injection. |

Confirmed correct: the precedence order, `user-invocable` as the correct spelling, `name`
optional and defaulting to the directory name, `description` recommended with a
first-paragraph fallback, the 500-line figure, three-level progressive disclosure,
nested/monorepo discovery, live change detection, the `--add-dir` exception, the string
substitutions listed, and — from v4.0 — the `disallowed-tools` version floor below.

## Version floors

From the [release notes](https://github.com/anthropics/claude-code/releases), which is where
floors live; the docs page carries only some of them.

| Feature | Floor |
|---|---|
| `disallowed-tools` in skill/command frontmatter | **v2.1.152** (27 May 2026) — *"Skills and slash commands can now set `disallowed-tools` in frontmatter to remove tools from the model while the skill is active"* |
| `/reload-skills` | **v2.1.152** — *"re-scan skill directories without restarting the session"* |
| `${CLAUDE_SKILL_DIR}` in `allowed-tools` | v2.1.129 |
| `${CLAUDE_PROJECT_DIR}` substitution | v2.1.196 |
| Skill stacking (`/a /b`) | v2.1.199 |
| Re-invocation dedupe | v2.1.202 |
| Directory-qualified nested skills | v2.1.203 |
| `background`, boolean aliases (`yes`/`no`/`on`/`off`/`1`/`0`) | v2.1.218 |

## Known unknowns

Recorded rather than guessed. If you need one of these, test it and update this file.

- **Stacked skills with conflicting tool fields.** Several skills can be stacked in one
  message (`/write-tests /fix-issue 123`, v2.1.199+). What happens when one sets
  `disallowed-tools` and another does not is not documented.
- **`SKILL.md` filename case sensitivity.** Every example uses `SKILL.md`; no explicit
  statement about case handling exists. Use the exact case.
