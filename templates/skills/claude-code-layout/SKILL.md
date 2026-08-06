---
name: claude-code-layout
description: Where Claude Code configuration must live to be loaded at all. Use when adding or moving a skill, subagent, command, rule, workflow, hook or settings file, when a piece of configuration seems to have no effect, or when reviewing whether a project's .claude/ directory is wired correctly. Covers the discovered-vs-registered distinction, the two precedence orders, and the layout the docs specify.
---

# Where Claude Code configuration lives

Verified 2026-08-06 against Claude Code v2.1.223.

A misplaced config file does not error. It is read by nothing, reports nothing, and leaves
every document that describes it looking correct. This repository has shipped that defect three
times — skills in a directory nobody scans, an adopter template with no `PreToolUse` guard, and
a settings file ignored only on one machine. All three passed every test at the time.

So the question this skill exists to make you ask, before anything else:

> **If this silently stopped being read, what would I observe?**

If the answer is "nothing", that is the finding. Go make it observable.

## The distinction that decides everything

| | How it is wired | How it fails |
|---|---|---|
| **Discovered by location** — `skills/`, `agents/`, `commands/`, `output-styles/`, `rules/`, `workflows/` | The directory and file name *are* the wiring | Put it anywhere else and it is inert |
| **Registered elsewhere** — **hooks** | A `settings.json` entry names the script; the script's own location is free | Miss the registration and the code is unreachable |

Both fail silently, in opposite directions. Moving a hook script is safe; moving a skill is not.
Deleting a hook's registration is fatal; a skill has no registration to delete.

**There is no `.claude/hooks/` discovery.** Hooks live under the `hooks` key of `settings.json`.
A `hooks/hooks.json` file is *plugin* structure — several third-party guides get this wrong, and
following them unwires the guard while leaving the script in place.

## The layout

```
your-project/
├── CLAUDE.md                    Project instructions, every session          [committed]
├── .mcp.json                    Project-scoped MCP servers — repo ROOT       [committed]
├── .worktreeinclude             Gitignored files to copy into new worktrees  [committed]
└── .claude/
    ├── settings.json            Permissions, hooks, config                   [committed]
    ├── settings.local.json      Personal overrides                    [MUST be gitignored]
    ├── rules/*.md               Topic-scoped instructions, optionally gated by file paths
    ├── skills/<name>/SKILL.md   Directory name = /command; supporting files alongside
    ├── commands/<name>.md       Reusable prompts; merged into skills, skill wins on a tie
    ├── output-styles/           Custom system-prompt sections
    ├── agents/<any>.md          Scanned RECURSIVELY. Identity = `name` frontmatter, NOT the
    │                            filename. Unique tree-wide; `name` cannot contain ':'
    ├── workflows/*.js           Dynamic subagent orchestration (v2.1.154+)
    └── agent-memory/<agent>/MEMORY.md   Subagent memory, written automatically

~/
├── .claude.json                 App state, OAuth, MCP user scope, per-project state
└── .claude/
    ├── CLAUDE.md · settings.json · keybindings.json · themes/
    ├── rules/ · skills/ · commands/ · output-styles/ · agents/ · workflows/
    └── projects/<project>/memory/MEMORY.md
```

Anything else directly under `.claude/` is ignored by Claude Code. That is allowed — this repo
keeps `workflow_config.json` there, read by its own hook via an explicit path — but it should be
a deliberate choice, not an accident. `tests/test_claude_layout.py` holds the allowlist.

## Two precedence orders, and they disagree

| For | Order |
|---|---|
| **Settings** | managed > CLI args > **local > project > user** |
| **Skills and other name collisions** | enterprise > **user > project** |

User and project are *inverted* between them. A single "precedence" mental model is wrong half
the time, so check which question you are asking.

## Before you add or move anything

1. **Is it discovered or registered?** Use the table above. Getting this backwards is the whole
   failure class.
2. **If discovered:** is it at the exact documented path, with the exact filename case?
3. **If registered:** does the registration exist, in *every* settings file that ships — the
   one you use and the one you distribute? A template that drifts from the config you dogfood
   is a config nobody tests.
4. **Prove it loads.** Not "the file is correct" — *observe* it working: the skill appears in
   the listing, the guard denies the command, the hook's context shows up.
5. Run `python -m unittest tests.test_claude_layout`.

## When something has no effect

- **A skill doesn't appear:** it is probably not under `.claude/skills/`. If it is, the
  directory may be newer than the session — run `/reload-skills` (v2.1.152+).
- **A hook never fires:** check its event is registered in `settings.json`, its `matcher`
  covers the tool, and the command path resolves. A `Bash`-only matcher misses the
  PowerShell tool on Windows.
- **A subagent is ignored:** identity comes from the `name` frontmatter, not the filename.
  Duplicate names across the tree resolve by filesystem read order, with no defined precedence.
- **A frontmatter field does nothing:** it is probably not a real field. Unrecognised keys are
  ignored silently — see [skill-authoring](../skill-authoring/SKILL.md).

## Reference files

- [references/directory-map.md](references/directory-map.md) — every path, what reads it, and
  what happens when it is misplaced.
- [references/frontmatter-by-type.md](references/frontmatter-by-type.md) — skills vs agents vs
  commands. The fields genuinely differ; `disallowed-tools` and `disallowedTools` are two
  different spellings for two different artifacts.

Hook *event* names are deliberately not listed here: there are 31 and they change release by
release, so a copy would be stale on arrival. Read
<https://code.claude.com/docs/en/hooks>. The one checked copy lives in
`tests/test_claude_layout.py::HOOK_EVENTS`, where a stale entry fails the build instead of
misleading a reader. For writing the skill itself rather than placing it,
see [skill-authoring](../skill-authoring/SKILL.md).

## Who orchestrates

Two modes, and the difference decides where intermediate results live:

| | Subagents · skills · agent teams | Dynamic workflows (`.claude/workflows/*.js`) |
|---|---|---|
| Decides what runs next | **Claude**, turn by turn | **The script** |
| Intermediate results land in | Claude's context window | Script variables |
| What is reusable | The worker definition | The orchestration itself |

So a long fan-out through subagents fills the context it was meant to protect, while a workflow
returns only the final answer. `ultracode` sets effort to `xhigh` and lets Claude choose a
workflow on its own.

## Provenance

This skill is the operative artifact — it is what Claude Code loads. The project's designated
golden-rule document is [`docs/claude-code-layout-guide/`](../../../docs/claude-code-layout-guide/index.md),
which also records three verified errors in the guide as received, including a hook-event
blocking table contradicted by this repository's own running `Stop` hook. Where that document
and the live docs disagree, the live docs win; where the running system disagrees with both,
the running system wins.
