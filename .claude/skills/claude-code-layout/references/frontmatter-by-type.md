# Frontmatter by artifact type

Skills, subagents and commands all use YAML frontmatter, and their fields are **not the same**.
The near-misses below are the expensive ones: an unrecognised key is ignored silently, so a
field borrowed from the wrong artifact does nothing and says nothing.

Verified 2026-08-06 against Claude Code v2.1.221.

## The near-misses

| You might write | Correct for | Because |
|---|---|---|
| `disallowedTools` in a **skill** | subagents | Skills use `disallowed-tools` (hyphenated) |
| `disallowed-tools` in a **subagent** | skills | Subagents use `disallowedTools` (camelCase) |
| `user-invokable` | — | The field is `user-invocable`, with a **c** |
| `version` | — | Not a field on any of them |
| `tools:` in a **skill** | subagents | Skills use `allowed-tools` / `disallowed-tools` |
| `model` expecting it to persist | — | On a skill it lasts the current turn only |

## Skills — `.claude/skills/<name>/SKILL.md`

`name` optional (defaults to the directory name; in a project skill it changes only the display
label, never the command). `description` recommended — it is the whole basis for automatic
invocation.

`when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`,
`allowed-tools`, `disallowed-tools` (v2.1.152+), `model`, `effort`, `context`, `agent`,
`background` (v2.1.218+), `hooks`, `paths`, `shell`.

Full descriptions: [skill-authoring/references/frontmatter-fields.md](../../skill-authoring/references/frontmatter-fields.md).

## Subagents — `.claude/agents/<any>.md`

| Field | Required | Notes |
|---|---|---|
| `name` | **Yes** | Lowercase and hyphens. **This is the identity, not the filename.** Cannot contain `:`. Must be unique across the whole tree — duplicates in one directory resolve by filesystem read order with no defined precedence |
| `description` | **Yes** | When Claude should delegate to it |
| `tools` | No | Inherits every subagent tool if omitted. If nothing in the list resolves, the subagent usually fails to launch |
| `disallowedTools` | No | camelCase here |
| `model` | No | `sonnet`, `opus`, `haiku`, `fable`, a full id, or `inherit` (default) |
| `permissionMode` | No | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, `manual` |
| `skills` | No | Skills **preloaded** into the subagent at startup — full content, not just the description. A skill with `disable-model-invocation: true` cannot be preloaded |
| `color` | No | Display colour in the task list |

Note the two differences from skills that catch people: `name` and `description` are
**required** here, and the directory is scanned **recursively** — subfolders organise files
without affecting identity.

## Commands — `.claude/commands/<name>.md`

Plain markdown; the **filename** is the command. Merged into skills and supporting the same
frontmatter, but with no directory for supporting files. A skill of the same name wins. Prefer a
skill for anything new.

## Not verified

`effort` and `maxTurns` on subagents appear in third-party guides but are not in the documented
field table. Do not rely on them without checking.
