# Frontmatter by artifact type

Skills, subagents and commands all use YAML frontmatter, and their fields are **not the same**.
The near-misses below are the expensive ones: an unrecognised key is ignored silently, so a
field borrowed from the wrong artifact does nothing and says nothing.

Verified 2026-08-06 against Claude Code v2.1.223.

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
`background` (v2.1.218+), `hooks`, `paths`, `shell`, `metadata`, `license`, `compatibility`.

The last three are accepted but inert: `metadata` is a free-form map for your own tooling,
`license` and `compatibility` come from the Agent Skills spec and Claude Code does not act on
either. `description` + `when_to_use` are truncated at **1,536 characters** in the listing, so
the key use case goes first.

Boolean fields accept `yes`, `no`, `on`, `off`, `1`, `0` in any case as well as `true`/`false`
— **as of v2.1.218**. Before that only `true`/`false` parsed, and anything else was silently
ignored, which is the usual failure shape.

Full descriptions: [skill-authoring/references/frontmatter-fields.md](../../skill-authoring/references/frontmatter-fields.md).

## Subagents — `.claude/agents/<any>.md`

| Field | Required | Notes |
|---|---|---|
| `name` | **Yes** | Lowercase and hyphens. **This is the identity, not the filename.** Cannot contain `:` — **as of v2.1.218 the file is not loaded at all** and the error goes only to the debug log; before that such names were accepted. Must be unique across the tree; duplicates resolve by filesystem read order with no defined precedence |
| `description` | **Yes** | When Claude should delegate to it |
| `tools` | No | Inherits every subagent tool if omitted. If nothing in the list resolves, the subagent usually fails to launch. To preload skills use `skills`, not `Skill` here |
| `disallowedTools` | No | camelCase here. Applied **first**, then `tools` resolves against what remains; a tool in both is removed. Accepts `mcp__<server>` patterns, and `mcp__*` removes every MCP tool |
| `model` | No | `sonnet`, `opus`, `haiku`, `fable`, a full id, or `inherit` (default) |
| `permissionMode` | No | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`, `manual` (alias for `default`, v2.1.200+) |
| `maxTurns` | No | Maximum agentic turns before the subagent stops |
| `skills` | No | Skills **preloaded** into the subagent at startup — full content, not just the description. A skill with `disable-model-invocation: true` cannot be preloaded |
| `mcpServers` | No | Server names or inline definitions |
| `hooks` | No | Lifecycle hooks scoped to this subagent |
| `memory` | No | `user`, `project` or `local` — enables cross-session learning |
| `background` | No | `true` always runs it in the background. Unset lets Claude choose, and **as of v2.1.198 the default is background** |
| `effort` | No | `low`…`max`, overriding session effort |
| `isolation` | No | `worktree` gives it an isolated checkout, branched from the **default branch**, not the parent's `HEAD` |
| `color` | No | Display colour in the task list |
| `initialPrompt` | No | Only when run as the main session agent via `--agent` |

Three differences from skills that catch people: `name` and `description` are **required**
here, the directory is scanned **recursively** (subfolders organise files without affecting
identity), and `permissionMode` / `hooks` / `mcpServers` are **silently ignored** for plugin
subagents.

## Commands — `.claude/commands/<name>.md`

Plain markdown; the **filename** is the command. Merged into skills and supporting the same
frontmatter, but with no directory for supporting files. A skill of the same name wins. Prefer a
skill for anything new.

## Corrected 2026-08-06

This file previously listed `effort` and `maxTurns` under "Not verified", on the grounds that
they appeared in third-party guides but not in the documented field table. **Both are in the
table** at `/docs/en/sub-agents#supported-frontmatter-fields`, and are now recorded above. The
entry was written from an incomplete read of the page, not from the page being wrong — the same
mistake `skill-authoring/references/verified-facts.md` records about `disallowed-tools`. Absence
of evidence was twice recorded as evidence of absence; re-read the whole table before writing
"not documented" again.
