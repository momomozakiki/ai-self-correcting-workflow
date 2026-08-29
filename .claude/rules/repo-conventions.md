# Repository conventions

Loaded every session. These are facts about how this repository is built that are expensive to
rediscover and easy to violate in a single edit.

## Dependencies

**Tests and the hook stay dependency-free.** The dispatcher is stdlib-only so adopters can
vendor it without inheriting a dependency tree — including the JSON-Schema validator, which is
a hand-written subset rather than `jsonschema`. Run:

```
python -m unittest discover -s tests
```

Anything that would add an import outside the standard library needs a different design.

## The four documents that drift

When hook behaviour changes, update these **together**:

- `.claude/hooks/workflow_hook.py`
- `schemas/hook_contract.md` — the **only** place the state-key list lives
- `GUIDE.md` §7
- `.claude/skills/adaptive-workflow/SKILL.md`

## Health check

```
python .claude/hooks/workflow_hook.py --self-test
```

Validates the config and reports health checks. **Exit 0 is not proof it ran** — check for
`[ ok ] config valid against schemas/config_schema.json`. A `validation skipped` warning also
exits 0, and once did so for two knowingly-invalid configs.

Two changes on 2026-08-29. The **governance maturity level is gone**: it rewrote a tracked file
on every run, so running the suite dirtied the tree. `--self-test` now writes nothing at all,
and `test_hook.TestSelfTest.test_self_test_does_not_write_to_the_repository` holds it to that
by diffing the file tree either side of a run. And the checklist-source line now reports **how
many items it examined** — it used to print `[ ok ] checklist sources validated` over an empty
directory, a pass earned by checking nothing.

## Autonomous runs

`.claude/skills/autonomous-task/SKILL.md` removes `AskUserQuestion` for the turn and says what
to do instead: read the repo, then the official docs, then take the conservative option and
record the assumption. It ends by invoking the `handover` skill, which writes
`plans/HANDOVER.md` — the user's entire view of a run they did not watch.

Autonomy means not asking the user to arbitrate. It is **not** licence to click through a
guard's `ask`.

## Runtime

Claude Code on a Claude Pro subscription, no API key (`GUIDE.md` §14). Sonnet 5 for routine
work, `/model opus` for hard passes. **Fable 5 bills usage credits on Pro — never make it a
default anywhere.**

## Commit hygiene

`git add -A` sweeps in `plans/UNFINISHED.md`, which the Stop hook rewrites on every dirty-tree
turn. It is transient session state and has been committed by accident twice. The path is
deliberately **not** gitignored, because a human-authored plan lives there too. So check before
staging: if `head -1 plans/UNFINISHED.md` shows `<!-- workflow-hook: auto-breadcrumb -->`, do
not commit it. Recover with `git rm --cached plans/UNFINISHED.md`.

## No heredoc stdin

Write scripts to a file and run the file; use the editing tools for source changes. Escapes get
mangled silently. For git: `git commit -m` (repeatable) or `-F <file>` — never `-F -`, a
heredoc, or a bare `git commit`. The guard returns `ask` on all four forms, but an `ask` that
the environment does not surface is not a safety net; the discipline is yours.
