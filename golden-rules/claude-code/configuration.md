# Claude Code configuration — golden rules

Status: drafted by orchestrator 2026-08-30, unreviewed
Applies when adding or moving a skill, subagent, command, rule, hook or settings file.

## Before writing the file

- [ ] Confirm the directory is one Claude Code actually scans. `.claude/agents/`,
      `.claude/skills/`, `.claude/commands/`, `.claude/rules/` are discovered **by location** —
      the same file elsewhere is inert, with no error and every frontmatter field dead.
- [ ] Check each frontmatter key against a verified field list, not memory. An unrecognised key
      is ignored **silently**. The expensive near-misses are case and hyphenation:
      subagents use `disallowedTools`, skills use `disallowed-tools`.
- [ ] A hook is different: it is **registered**, not discovered. Its script location is free,
      but without a `settings.json` entry the code is unreachable.

Sources: Claude Code docs, sub-agents (code.claude.com, retrieved 2026-08-29); this repo's
`.claude/skills/claude-code-layout/references/frontmatter-by-type.md`.

## Before depending on what you just created

- [ ] **Invoke it.** A subagent, skill or hook that has never run is indistinguishable from one
      that does not exist.
- [ ] Expect a **newly written subagent to be undiscoverable in the session that wrote it** —
      `.claude/agents/` is scanned at session start. Plan the restart into the work rather than
      discovering it at the moment you need the agent.
- [ ] `/reload-skills` (v2.1.152+) covers **skills**. Do not assume it covers subagents.
- [ ] If the thing cannot be exercised yet, say so explicitly and mark what it would take.
      An untested verifier is not a verifier.

Sources: Incident 2026-08-29 — `stage-gate-auditor` was written, correctly placed, correctly
mirrored, and passed every test in the suite, then failed to dispatch:
`Agent type 'stage-gate-auditor' not found`. The agent whose entire purpose was to
independently certify later work could not be certified itself, and the gap was found only at
the moment of use.

## When the artifact ships to others

- [ ] If the repo mirrors `.claude/**` into `templates/**`, the mirror is **part of the edit**,
      in the same commit. Adopters read the template copy.
- [ ] Verify byte-identity rather than trusting the copy: `cmp <source> <template>`.

Sources: Incident 2026-08-06 (recurring) — `templates/settings.json.hooks`, the fragment
adopters merge, carried no `PreToolUse` block at all while four prohibitions declared
themselves `live` and the suite stayed green throughout; recorded in `docs/RETROSPECTIVE.md`.

## Questions worth asking

- [ ] If this configuration silently stopped being read, what would I observe? If the answer is
      "nothing", that is the finding.
- [ ] Does a passing test prove this runs, or only that the file parses?
- [ ] Is the thing that claims to enforce something actually wired to a real event?

Sources: reasoned from first principles, 2026-08-29; the question is this repo's own
`layout-auditor` framing.
