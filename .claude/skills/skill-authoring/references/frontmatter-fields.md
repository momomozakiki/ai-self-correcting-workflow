# Frontmatter fields and string substitutions

Source: <https://code.claude.com/docs/en/skills> — "Frontmatter reference" and "Available
string substitutions". Verified 2026-08-06 against Claude Code v2.1.223.

**All fields are optional.** Only `description` is recommended, so Claude knows when to use
the skill. Any key not in this table is ignored silently — no error, no warning.

Boolean fields accept `yes`, `no`, `on`, `off`, `1`, `0` in any letter case as well as `true`
and `false` (aliases require v2.1.218+; before that, only `true`/`false`).

## Fields

| Field | What it does |
|---|---|
| `name` | Display label in skill listings. Defaults to the directory name. In a personal or project skill it does **not** change the command — the directory name does. In a plugin skill it sets the last command segment. |
| `description` | What the skill does and when to use it. Drives automatic invocation. `description` + `when_to_use` are truncated at **1,536 characters** in the listing. If omitted, the first paragraph of the body is used. |
| `when_to_use` | Extra trigger phrases or example requests, appended to `description` in the listing and counting toward the same 1,536-character cap. |
| `argument-hint` | Autocomplete hint, e.g. `[issue-number]` or `[filename] [format]`. |
| `arguments` | Named positional arguments for `$name` substitution. Space-separated string or YAML list; names map to positions in order. |
| `disable-model-invocation` | `true` stops Claude loading the skill automatically — only `/name` invokes it. Also removes it from subagent preloading, and (v2.1.196+) stops a scheduled task firing it. Default `false`. |
| `user-invocable` | `false` hides it from the `/` menu; Claude can still invoke it. Default `true`. Note: this controls menu visibility only, not programmatic access — use `disable-model-invocation` to block that. |
| `allowed-tools` | Tools usable without a permission prompt **during the invoking turn only**; the grant clears on your next message. Space- or comma-separated, or a YAML list. In a project skill it takes effect only after the workspace trust dialog is accepted. |
| `disallowed-tools` | Tools removed from the pool while the skill is active; clears on your next message. Cannot remove `EndConversation` while any other tool remains. **Requires v2.1.152+** (release notes, 27 May 2026 — the docs page states no floor). |
| `model` | Model for the rest of the current turn; not saved to settings. Accepts `/model` values or `inherit`. |
| `effort` | `low` / `medium` / `high` / `xhigh` / `max`, depending on the model. Overrides the session level. |
| `context` | `fork` runs the skill in a forked subagent. The skill body becomes the subagent's prompt, with no access to conversation history. |
| `agent` | Which subagent type to use when `context: fork` is set. |
| `background` | With `context: fork` only. `false` waits for the result in the invoking turn instead of backgrounding it. Default `true`. Requires v2.1.218+. |
| `hooks` | Hooks scoped to this skill's lifecycle. |
| `paths` | Glob patterns limiting automatic activation to matching files. |
| `shell` | `bash` (default) or `powershell`, for `` !`command` `` injection in this skill. |

`context: fork` only makes sense for a skill with an actionable task. A guidelines-only skill
handed to a subagent produces a subagent with guidelines and nothing to do.

## String substitutions

| Variable | Expands to |
|---|---|
| `$ARGUMENTS` | All arguments. If absent from the body, arguments are appended as `ARGUMENTS: <value>`. |
| `$ARGUMENTS[N]` | One argument by 0-based index. |
| `$N` | Shorthand for `$ARGUMENTS[N]` — `$0`, `$1`. |
| `$name` | A named argument declared in `arguments`. |
| `${CLAUDE_SESSION_ID}` | Current session ID. |
| `${CLAUDE_EFFORT}` | Current effort level; ultracode reports as `xhigh`. |
| `${CLAUDE_SKILL_DIR}` | The directory holding this `SKILL.md`. Use it to reference bundled scripts regardless of cwd. Requires v2.1.129+ for the `allowed-tools` substitution. |
| `${CLAUDE_PROJECT_DIR}` | The project root, same value hooks receive. Requires v2.1.196+. |
| `` !`command` `` | Runs the command and substitutes its output before Claude sees the content. |

`${CLAUDE_SKILL_DIR}` and `${CLAUDE_PROJECT_DIR}` substitute in **two** places: the markdown
body and Bash rules in `allowed-tools`. Using the same variable in both lets a bundled script
run without a permission prompt:

```yaml
---
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/render.sh *)
---
Run `${CLAUDE_SKILL_DIR}/scripts/render.sh` to produce the chart.
```

## Fields from the open standard that Claude Code does not document

`license`, `compatibility` and `metadata` appear in the agentskills.io specification but not
in the Claude Code frontmatter reference. They are safe to omit; do not rely on them here.

## Fields that do not exist

`version` is **not** a Claude Code frontmatter field, despite appearing in third-party guides.
It is not in the reference above, so it is ignored silently — no error, no warning, no effect.
`tests/test_skills.py` rejects it for exactly that reason: the failure mode of an unrecognised
key is invisible, so the test has to be the thing that makes it visible. A skill's history
belongs in the ledger, not in a key nothing reads.
