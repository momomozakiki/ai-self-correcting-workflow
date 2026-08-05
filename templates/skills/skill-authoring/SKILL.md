---
name: skill-authoring
description: Structure, size and split a Claude Code skill. Use when creating a new skill, when an existing SKILL.md has grown past its budget, when deciding whether something should be one skill or several, or when choosing frontmatter fields. Covers the discovery locations that actually work, the progressive-disclosure layout, naming rules, and the tests that enforce them.
---

# Authoring a skill

One skill, one responsibility. A skill that needs "and" in its description is two skills.

Everything here is verified against the official documentation; the citations and check dates
are in [references/verified-facts.md](references/verified-facts.md). Don't restate a claim
about Claude Code behaviour from memory — look it up there, and if it isn't there, verify it
and add it.

## Where a skill must live

`.claude/skills/<skill-name>/SKILL.md`, committed to the repo. That path is not a convention —
it is one of the only three places Claude Code looks (personal `~/.claude/skills/`, project
`.claude/skills/`, and plugin directories).

**A skills directory anywhere else is not discovered.** A repo-root `skills/` folder loads
nothing, registers no `/command`, and silently ignores every frontmatter field in it. This
repository shipped exactly that mistake; `tests/test_skills.py` now fails if the old path
reappears anywhere.

The directory name is the command name: `.claude/skills/deploy-staging/` → `/deploy-staging`.

## The size rule, and why it is not really 500 lines

Two limits, and the smaller one is the one that bites:

| Limit | Value | Behaviour when exceeded |
|---|---|---|
| Documented body cap | 500 lines | The official recommendation. `tests/test_skills.py` **fails**. |
| Compaction re-attach | ~5,000 tokens | After auto-compaction only the **first 5,000 tokens** of each skill are restored. The rest is silently gone. The test **warns**. |

A 400-line skill can already be over the token budget. Measure characters, not lines: roughly
4 characters per token, so ~19,000 characters is the real ceiling. Past it, the tail of your
skill disappears at exactly the moment context is scarcest — and nothing tells you.

There is a second reason to stay small: an invoked skill's content enters the conversation
**once and stays there**. Claude Code does not re-read the file on later turns. Everything you
write is paying rent for the rest of the session.

## Splitting: what stays, what moves

Keep in `SKILL.md` anything that must apply without a second read — the decision procedure,
prohibitions, the steps themselves, and a map of what lives where.

Move to `references/` anything consulted only when a specific case arises: lookup tables, full
field references, format specifications, worked examples, background rationale.

```
skill-name/
├── SKILL.md            required, exact case
├── references/         loaded on demand — link each one from SKILL.md
├── scripts/            deterministic work: validation, generation, analysis
└── assets/             templates, configs, images
```

Link every reference from `SKILL.md` with a relative markdown link and say what it contains,
so the decision to load it can be made without loading it. Keep references **one level deep**
from `SKILL.md`; a reference that only another reference names is a reference nobody reads.

Split into a **separate skill** — not a reference — when the trigger differs. Two bodies of
knowledge used at different moments, by different requests, are two skills. Same trigger,
different depth, is one skill with references.

## Naming

- Directory: lowercase kebab-case, `^[a-z0-9]+(-[a-z0-9]+)*$`, ≤64 characters.
- No leading, trailing, or consecutive hyphens.
- `SKILL.md` in that exact case.
- References: lowercase with hyphens, `.md`.
- Frontmatter `name`, when present, must match the directory name. It is optional and defaults
  to the directory name; setting it to something else in a project skill changes only the
  display label, not the command, which is a trap worth avoiding.

## Frontmatter

`description` is the only field that really matters — it is all Claude sees when deciding
whether to load the skill. Write it in the third person, put the key use case **first**, and
name the triggering situations concretely. "Use when creating a new skill or when a SKILL.md
has grown past its budget" beats "helps with skills".

Every other field is optional. Use one only when you can say what it changes:

- `disable-model-invocation: true` — only a human should trigger this (deploys, commits, sends).
- `user-invocable: false` — background knowledge with no meaningful `/command`.
- `allowed-tools` / `disallowed-tools` — pre-approve or remove tools for the invoking turn.
- `context: fork` + `agent` — run in a subagent so research noise stays out of the main context.

The full verified table, plus string substitutions like `${CLAUDE_SKILL_DIR}`, is in
[references/frontmatter-fields.md](references/frontmatter-fields.md). **Any key not on that
list is ignored silently** — a misspelled `user-invokable` does nothing and reports nothing,
which is why `tests/test_skills.py` rejects unknown keys.

## Writing style

Imperative and direct: "Parse the config file", not "You should parse the config file". Assume
the reader is competent — supply the context they cannot have, not the reasoning they can do.
Because the content persists for the whole session, write standing instructions rather than
one-time steps.

For a review or judgement skill, phrase items as **questions**, not prescriptions. "Does this
class have one reason to change?" survives contact with a codebase it wasn't written for;
"use an interface for every service" does not. The same rule governs `.ai/` checklists — see
`.ai/GROWTH.md`.

## Before you finish

1. `python -m unittest tests.test_skills` — naming, size, frontmatter keys, link resolution.
2. Mirror `.claude/skills/` into `templates/skills/` in the same commit. Adopters copy from
   there; the parity test fails otherwise.
3. Skills carry **no** doc-standard frontmatter (no `version`/`last_validated`) — their
   frontmatter belongs to Claude Code's schema. The ledger traces their history instead.
4. Log the change in `history/YYYY-Www.md`.
5. If the skills directory is newly created at the top level, **restart Claude Code** — a
   skills directory that did not exist at session start is not watched.

## Reference files

- [references/frontmatter-fields.md](references/frontmatter-fields.md) — every documented
  frontmatter field and string substitution, with what each one actually does.
- [references/verified-facts.md](references/verified-facts.md) — discovery, precedence,
  lifecycle and budget facts with source URLs and check dates, plus the known unknowns.
