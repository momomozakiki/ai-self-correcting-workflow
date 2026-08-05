# Documentation Standard — frontmatter, sidecars, folding

Mandatory for every doc you create or update. Full spec: `GUIDE.md` §6.

## Markdown / HTML frontmatter

Place at the very top of the file:

```markdown
---
title: <Title>
version: 1.0                     # bump MINOR for content, MAJOR for restructure
last_validated: YYYY-MM-DD       # date you last re-confirmed the CONTENT is correct
official: false                  # true | false | unknown
source: agent-generated          # URL | agent-generated | user-provided, origin unknown
tags: [<retrieval tags>]
applies_when: "<when this doc is relevant>"
estimated_tokens: <int>
---

# <Title>
**Version 1.0** — *<one-line scope>*

## Revision History
| Version | Date       | Change   |
|---------|------------|----------|
| 1.0     | YYYY-MM-DD | Initial. |
```

## The two rules people get wrong

**`last_validated` refreshes only when you re-confirm the content is correct** — a content
review. A mechanical edit, or a frontmatter-only edit, leaves it unchanged. Otherwise the
field overstates when the content was last actually checked, which is worse than having no
field at all.

**Provenance is asked for, not assumed.** For an external doc, ask "Is this from an
official/authoritative source? URL?" and set `official`/`source` from the answer.
Agent-generated docs get `official: false` and today's `last_validated` when the content is
authored or reviewed now — *not* for a frontmatter backfill onto pre-existing content. If it
is unconfirmed, mark `official: unknown`. Never invent a source.

## Sidecar provenance (JSON, code, other non-commentable formats)

`config.json` → `config.json.prov.md`:

```markdown
# Provenance for config.json
- version: 1.0
- last_validated: YYYY-MM-DD
- official: false
- source: agent-generated
- notes: ...
```

One provenance record per artifact, embedded in the artifact wherever the format allows it.
`.ai/` rule files carry a `provenance` block inside the JSON instead of a sidecar, which is
exactly what the sidecar convention exists to substitute for.

## Folding a doc into a folder (GUIDE §6.4)

A flat `docs/<name>.md` folds into `docs/<name>/` when it:

- breaks the "Rule of One Question", or
- exceeds its layer's token budget, or
- has an in-file Revision History past ~8 rows.

Split per `docs/Progressive Disclosure Documentation Guide.md`: `index.md` holds the canonical
frontmatter, children carry lightweight frontmatter plus a link back.

On folding, relocate the full history to a sibling `CHANGELOG.md` (copy
`templates/docs/CHANGELOG_TEMPLATE.md`) and keep only the latest ≤3 rows plus a link in
`index.md`. That `CHANGELOG.md` is a sibling peer marked `exclude_from_ai: true`, so it stays
out of the active token budget.

## What is exempt

Skill files (`.claude/skills/*/SKILL.md` and their `references/`) carry **no** doc frontmatter.
They live under `source_directories`, not `documentation_directories`, and their frontmatter
is Claude Code's schema — adding `version`/`last_validated` there would put an unrecognised
key in a file that a real parser reads. Their history is traced by the ledger.
