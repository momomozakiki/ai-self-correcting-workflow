---
name: autonomous-task
description: Run a task end to end without stopping to ask. Use when the user wants the whole job done in one pass — researching best practice where the answer is unknown, auditing the work against the golden-rule checklists in .ai/05-domains/, and handing back a single review checklist at the end instead of interrupting mid-task.
disallowed-tools: AskUserQuestion
---

# Autonomous task execution

You are running a task to completion without checking in. `AskUserQuestion` is removed
from your tool pool for this turn, so the option is not available — that is deliberate.
Everything below is about what to do *instead* of asking.

The restriction clears on the next user message. It does not make you unaccountable: it
moves the review from the middle of the work to the end of it, which raises the bar on
the handover, not lowers it.

## What this does not override

**Tier 0 stays absolute.** Never force-push a shared branch, commit secrets, rewrite
published history, or delete the ledger or plan archive. The `PreToolUse` guard denies
the first and the last of these outright; the other two escalate. **If a guard escalates,
that is not a prompt to click through.** The guard asking is the signal that the *action*
is wrong, not that the approval is missing — an `ask` waved through has already broken a
rule once in this repository's history (`docs/RETROSPECTIVE.md`, 2026-08-05). Change the
approach.

Autonomy is about not asking *the user* to arbitrate. It is not permission to route
around a control.

## Deciding instead of asking

When you hit a fork you would normally raise:

1. **Can the repository answer it?** Read the code, the ledger, `docs/`, `.ai/`. Most
   questions worth asking are already decided somewhere.
2. **Can official documentation answer it?** Research it. Prefer the vendor's own docs
   over blogs and forums; quote the passage you relied on so the decision is auditable.
   If two sources disagree, say which you followed and why.
3. **Still open?** Take the **conservative** option — the one that is easier to reverse,
   claims less, or fails safe — and record the assumption in the handover. A reversible
   wrong choice costs less than a blocked task.

Only stop for something genuinely destructive and irreversible that the user has not
authorised. That is a *report*, not a question: say what you stopped at and why.

## Loading the right checklists

`.ai/05-domains/` holds ten review checklists. Loading all of them for a typo fix wastes
the context budget; loading none for a new API misses the point. **The selection rules are
data, in `.ai/05-domains/manifest.json` under `selection` — read them there.** They are
deliberately not restated here, because a copy is a second thing to keep right.

Two inputs you supply:

- **`task_size`** — declare it at Phase 1, before the work exists. It is a judgement, not a
  measurement: deriving it from `git diff --stat` would mean the diff is empty when you
  need the answer, and correct only once the code you were meant to guide is already
  written. Because it is a judgement, it goes in the handover for a human to confirm.
- **`tech_stack`** — what the project actually uses. A rule whose `tech_stack_required` is
  empty applies everywhere; otherwise it loads only on an intersection. This is what keeps
  SQL rules out of a NoSQL project.

Then answer the loaded items against the code you wrote, and report the answers —
including the ones that pass. A checklist that only ever surfaces problems reads as noise.

## Researching a golden rule

When the task touches a domain with no checklist in `.ai/05-domains/`:

- Research it, then write the checklist **as questions**, not prescriptions.
  *"Does this class have one reason to change?"* — not *"use interface X"*. A
  prescription tells you what to type; a question makes you look. The first survives
  contact with a codebase it was not written for; the second does not.
- Keep it general enough to apply to any project in that domain, specific enough that a
  violation is recognisable. If running it over real code finds nothing, it is too vague
  to keep.
- Tier it honestly. Nothing mechanically verifies "this class has one responsibility", so
  a review checklist is `convention` and says so in its `enforcement_note`.
- Cite provenance: source, date, and what you were trying to answer.
- Flag it in the handover as a **new rule proposed for ratification**. You wrote it
  yourself; the user has not agreed to it yet.

Isolate research that would flood the working context: a skill with `context: fork` and
`agent: Explore` returns the findings without the search noise.

## Reusing what already works

Before implementing a common pattern, check `.ai/06-components/` for a blueprint. If one
fits, use it and change only what it marks mutable. If you build something that survived
review and would be worth having again, propose it as a new blueprint in the handover —
but only after it has actually worked, not on the expectation that it will.

## The loop

Follow the Phase 0–3 discipline in `skills/adaptive-workflow/SKILL.md`. It is unchanged;
this skill only removes the mid-task check-in. Two points bear repeating because they are
where an unattended run goes wrong:

- **Log every intentional change to the weekly ledger.** Nobody is watching the reminder
  fire. Write the entry when you make the change, not from memory at the end.
- **Verify by trying to break it.** A test written until it passes proves nothing. Run a
  new check against the unfixed code first and record what failed.

## Finishing

Invoke the `handover` skill. The user's entire view of this run is the checklist it
writes, so it carries the decisions you made on their behalf, the assumptions you took,
what you could not verify, and anything awaiting ratification. Understating there is
worse than having asked in the first place.
