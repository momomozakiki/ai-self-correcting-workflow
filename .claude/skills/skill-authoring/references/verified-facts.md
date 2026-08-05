# Verified facts about Claude Code skills

Every claim below was checked against <https://code.claude.com/docs/en/skills> on
**2026-08-06**, against Claude Code **v2.1.221**. Re-verify before trusting any of it in a
later version; several of these carry explicit version floors, which is evidence the surface
moves.

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

## Live change detection

Claude Code watches skill directories and picks up added, edited or removed skills within the
session, with no restart. **Exception:** a top-level skills directory that did not exist when
the session started is not watched — creating one requires a restart.

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

Confirmed correct in that guide: the precedence order, `user-invocable` as the correct
spelling, `name` optional and defaulting to the directory name, `description` recommended with
a first-paragraph fallback, the 500-line figure, three-level progressive disclosure,
nested/monorepo discovery, live change detection, the `--add-dir` exception, and the string
substitutions it does list.

## Known unknowns

Recorded rather than guessed. If you need one of these, test it and update this file.

- **Minimum version for `disallowed-tools`.** The docs annotate version floors elsewhere
  meticulously (`background` v2.1.218, `${CLAUDE_PROJECT_DIR}` v2.1.196, boolean aliases
  v2.1.218) and give none for `disallowed-tools`. No floor is documented; it is verified
  working on v2.1.221 and nothing more can honestly be said.
- **Stacked skills with conflicting tool fields.** Several skills can be stacked in one
  message (`/write-tests /fix-issue 123`, v2.1.199+). What happens when one sets
  `disallowed-tools` and another does not is not documented.
- **`SKILL.md` filename case sensitivity.** Every example uses `SKILL.md`; no explicit
  statement about case handling exists. Use the exact case.
