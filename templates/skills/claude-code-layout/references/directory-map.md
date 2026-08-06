# Directory map — what reads each path, and how it fails

Verified 2026-08-06 against Claude Code v2.1.223, from
<https://code.claude.com/docs/en/claude-directory>, `/docs/en/skills`, `/docs/en/hooks`,
`/docs/en/sub-agents`, `/docs/en/workflows` and `/docs/en/settings`.

The third column is the one that matters. Every entry there is silent — none of these produce
an error when misplaced.

## Project

| Path | Read by | If it is somewhere else |
|---|---|---|
| `CLAUDE.md` (root or `.claude/`) | Loaded into context every session | Not loaded; conventions silently unavailable |
| `.mcp.json` | MCP server config, **repo root** | Servers never start. Note it is *not* under `.claude/` |
| `.worktreeinclude` | Lists gitignored files to copy into new worktrees | New worktrees miss those files |
| `.claude/settings.json` | Permissions, hook registration, env | Nothing applies — including every hook |
| `.claude/settings.local.json` | Personal overrides | Must be gitignored; committing it publishes your permission grants |
| `.claude/rules/*.md` | Loaded alongside CLAUDE.md; can be gated by file path | Not loaded |
| `.claude/skills/<name>/SKILL.md` | Skill discovery. Directory name is the `/command` | **Inert.** No command, no auto-trigger, and every frontmatter field does nothing |
| `.claude/commands/<name>.md` | Slash commands. Filename is the command | No command. A same-named skill wins |
| `.claude/output-styles/` | System-prompt sections | Not applied |
| `.claude/agents/*.md` | Subagent discovery, **recursive** | Not delegated to. Identity is `name`, not the filename |
| `.claude/workflows/*.js` | Dynamic workflows (v2.1.154+) | Not invocable |
| `.claude/agent-memory/<agent>/MEMORY.md` | Subagent persistent memory, written automatically | Memory not carried between runs |

## User

| Path | Read by |
|---|---|
| `~/.claude.json` | App state, OAuth, MCP user scope, per-project state |
| `~/.claude/settings.json` | Defaults for every project |
| `~/.claude/CLAUDE.md` | Personal instructions everywhere |
| `~/.claude/keybindings.json` · `themes/` | Shortcuts, colours |
| `~/.claude/{rules,skills,commands,output-styles,agents,workflows}/` | Personal versions of each |
| `~/.claude/projects/<project>/memory/MEMORY.md` | Auto memory Claude maintains |

## Hooks — registered, not discovered

There is **no** `.claude/hooks/` discovery. Scripts run only because `settings.json` names them:

```json
{"hooks": {"PreToolUse": [{"matcher": "Bash|PowerShell",
  "hooks": [{"type": "command",
             "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/workflow_hook.py\""}]}]}}
```

- `${CLAUDE_PROJECT_DIR}` and `${CLAUDE_PLUGIN_ROOT}` make the path independent of the working
  directory. The docs use the braced form; the bare `$CLAUDE_PROJECT_DIR` also works.
- `matcher` is a regex over the tool name. Empty or absent means every tool. **A `Bash`-only
  matcher misses the PowerShell tool on Windows** — cover both.
- `.claude/hooks/` as a folder for the scripts is fine and conventional. It is the *registration*
  that wires them, not the folder.
- Hook *types*: `command`, `http`, `prompt`, `agent`, `mcp_tool`.
- `PreToolUse` blocks via JSON —
  `hookSpecificOutput.permissionDecision` ∈ `allow | deny | ask | defer`, with
  `permissionDecisionReason`. Exit code 2 is the general cross-event blocking path; for
  `PreToolUse` the JSON form is what the docs specify and what this repo's guard returns.
- Every project shipping a settings *template* has two configs to keep in step. Test both.

## Discovery subtleties worth knowing

- **Nested project skills and agents** load from `.claude/` directories below the working
  directory. Skills there are not loaded at startup — they appear the first time Claude reads or
  edits a file in that subdirectory, under a directory-qualified name like `/apps/web:deploy`.
- **Parent directories** are scanned too: starting Claude in a subdirectory still picks up
  `.claude/skills/` at the repository root.
- **`--add-dir` / `/add-dir`** load `.claude/skills/` from the added directory — an explicit
  exception to the rule that additional directories grant file access, not configuration.
  `permissions.additionalDirectories` in settings does **not** do this.
- **Symlinks** are followed for a skill directory, and the skill loads once even if reachable
  from several locations.
- **Live change detection** covers `SKILL.md` text within the session — except a top-level
  skills directory created after the session started, which is not watched. `/reload-skills`
  (v2.1.152+) re-scans without losing the conversation.
- **Plugins** namespace everything as `plugin-name:item`, so they never collide.
