# Growing this library

Status: drafted by orchestrator 2026-08-30, unreviewed

This library is **seeded empty rather than pre-filled**. A rule nobody hit yet is a guess; a
rule harvested from a real mistake is knowledge. Everything here is about how items get in,
how they are trialled before they stay, and — the part nobody does voluntarily — how they get
out.

`AUTHORING-GUIDE.md` is how to write an item well. This is when one is allowed to exist.

## Which file a checklist belongs in — the altitude question, again

Two kinds of checklist, and the distinction is not cosmetic:

| Kind | Reviews | Gated on tech stack? |
|---|---|---|
| `planning/` | The **plan**, before code exists | Never |
| `<domain>/` | The **code**, once it does | Yes, where it applies |

A domain checklist reviews code *against* the plan, so it structurally cannot see a defect *in*
the plan. It will happily confirm that a well-built thing was built well when the thing should
not have been built at all.

**The test: if your question is answerable before any code is written, it belongs in
`planning/`.** "Is the rollback path stated?" is a planning question. "Does the rollback script
actually run?" is a domain question.

Sources: `.ai/GROWTH.md` v1.4 (2026-08-05), the folder-altitude section, ported 2026-08-30.

## How an item gets in

Three routes, and only three.

**Breadth — a domain with no rules at all.** A task needed one. Create
`golden-rules/<domain>/<file>.md` and write the rules you actually needed. Do not speculate
beyond them. An empty domain is an honest state; a domain padded to look complete is not.

**Depth — an edge case inside a domain that already exists.** Add the item to the group whose
*when* it belongs to. If no group fits, the group is the finding, not the item.

**Research — a domain the repository has not learned yet.** No checklist exists and no mistake
has been made, so neither breadth nor depth applies. Research the golden rule rather than
inventing one, cite it version-pinned per `AUTHORING-GUIDE.md`, and — this is the part that
matters — **never assume, never guess, never work from memory.** Where no authority exists,
`Source: reasoned from first principles, <date>` is the honest answer and it is a complete one.

A researched item is **proposed, not ratified**: it ships with
`Status: drafted by orchestrator <date>, unreviewed`, and whoever used it says so in their
report. A human deciding it stays is what turns it into `ratified`.

Sources: `.ai/GROWTH.md` v1.4 (2026-08-05), the three growth protocols, ported and trimmed
2026-08-30.

## Trial before keeping — the step that gets skipped

An item that has never been run against real work is a hypothesis in checklist clothing.

- Run a new or edited file against **real work**: real code for a domain file, a real plan for
  a planning file.
- Trial it against something **you** wrote, not something convenient. A checklist that flatters
  the work it shipped with has not been tested. `.ai/03-planning/` was first run against the
  plan that created it and returned ten findings on its own author — an absent out-of-scope
  list, an unstated rollback, and an unnamed assumption among them.
- **A checklist that finds nothing in a thousand lines is too vague to be worth loading**, and
  you will not discover that by reading it.
- Record what the trial found, **including which items did not apply**. Those are the next
  strike candidates.

Sources: `.ai/GROWTH.md` v1.4 (2026-08-05), trial-before-keeping; the ten-findings result is
this repository's own, recorded 2026-08-05.

## How an item gets out — and the one reason that is not allowed

Strike an item for exactly three reasons:

- **Unanswerable.** Nobody can tell whether it passed. It has been ticked without being
  checked for as long as it has existed.
- **Duplicative.** Another item already forces the same action. Two items, one decision.
- **Already tool-enforced.** A formatter, type checker, hook or test fails the build first. The
  item now costs attention and buys nothing.

**Never strike an item because it keeps passing.** This is the inversion that matters and it is
easy to get backwards: *a rule that prevents failures produces no failures.* "Struck if it
fired with nothing behind it" deletes precisely the rules that work and keeps the ones nobody
follows. Passing is the intended outcome, not evidence of uselessness.

Any strike appends one dated line to the growth ledger naming the file, the item and which of
the three reasons applied. A strike with no recorded reason is indistinguishable from an
accident.

Sources: design review of `plans/golden-rules-migration.md`, 2026-08-29 — the strike criterion
in the first draft was backwards and was rewritten to these three. Recorded there as a
correction carried in from the reviews.

## Promotion from a project layer — the two-occurrence threshold

A project layer (`plans/<project>/checklists/<domain>.md`) is where an agent's project-specific
items go. Most of them stay there and die with the project. Promotion into a golden base
requires **evidence, not judgement**:

- A mistake recorded **twice** in `docs/RETROSPECTIVE.md` stops being a note and becomes
  structure. Once is an incident; twice is a pattern.
- Or a **named failure** the item would have prevented, written down with its date.

Nothing else promotes. In particular an agent's own assessment that an item is good does not:
improvement here is **evidence-triggered**, because this repository already killed a loop where
the agent that applied a rule also decided its own false-positive rate. There was no ground
truth anywhere in it.

**Any edit to a golden base resets `Status:` to unreviewed.** Ratification is per-version, not
per-file — a stamp that outlives the content it described is drift with a signature on it.

Sources: `docs/checklist-system.md` §6, which lists confidence self-adjustment in its
**dropped** table; `.ai/GROWTH.md` v1.4 (2026-08-05), the self-hardening rule.
