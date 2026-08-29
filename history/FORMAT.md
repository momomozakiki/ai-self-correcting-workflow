# Change-History Ledger — Format

A weekly, chronological record of every **intentional** change to the project.
It is **not** a verbatim copy of `git log` — it captures what a reviewer would
care about, with the *why*.

## Files & rotation
- One file per ISO week: `history/YYYY-Www.md` (e.g. `history/2026-W28.md`).
- Create the file on the first qualifying change of the week.

## What to log
Log every intentional change with a purpose: feature work, bug fixes,
refactoring, documentation updates, configuration changes, important decisions.

**Do not log:** single-character typo fixes in comments, whitespace-only
changes, or trivial `.gitignore` tweaks that don't affect project logic. Rule of
thumb: *if a reviewer would care, log it.*

## Tag vocabulary
`[design]` `[doc]` `[code]` `[workflow]` `[config]` `[decision]` `[data]`

## Risk field (optional)

A change that carries real risk may add one `**Risk:**` line using one of five
fixed slugs:

| Slug | Covers |
|------|--------|
| `privilege` | Permissions, access scope, credentials, anything that widens what an agent can reach |
| `design` | Flawed planning or logic: missing validation, a gap in the workflow itself |
| `behavioral` | The agent acting unpredictably — loops, retries, drift from instructions |
| `structural` | Composition and interaction between agents or components; cascading failure |
| `accountability` | Ownership, auditability, traceability — who is answerable, and can you tell later |

**This list is the ledger's own, and is deliberately not the CISA five.** These slugs describe
risk from the *changing the repo* angle (`privilege`, `behavioral`) rather than the *acting
autonomously* angle, and they are frozen: entries already written use them, and rewriting the
vocabulary would invalidate history for no gain. Earlier revisions of this file described these
as the CISA categories, which was wrong.

The CISA taxonomy this used to contrast against — a `risk_source` field on rule files under
`.ai/`, validated against per-source weight bands — **was removed on 2026-08-29**. It was an
enterprise risk-register vocabulary, and deciding whether a checklist question was
`structural` or `accountability` was a judgement nobody could make the same way twice. A
taxonomy applied inconsistently is noise wearing the costume of rigour. The ledger's own list,
below, was always the one that carried its weight, and is unaffected.

Omit the line when a change carries no notable risk — an always-present field stops
carrying signal.

## Entry format

Substantial changes use the full form:

```markdown
# 2026-W28  (2026-07-06 – 2026-07-12)

## 2026-07-08
### [design] docs/artifact/Scale Indicator.dc.html
- **What:** Reworked ODB reference into full weighing-terminal layout.
- **Why:** Round-2 UI/UX pass.
- **Risk:** design — the layout drives operator actions; a wrong control placement misleads.
- **Refs:** plan `plans/archive/2026-07-08_scale-indicator/plan.md` · commit b30333d
```

Minor / routine changes get a one-line note under the day's heading:

```markdown
### [code] src/utils.py – minor: fixed typo in error message
```

## Reference field
Always include the abbreviated commit hash when available. For substantial
changes, also link the corresponding plan file by its relative path.
