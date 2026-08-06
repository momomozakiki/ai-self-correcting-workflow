---
name: handover
description: Write plans/HANDOVER.md — the review checklist for a task that ran without mid-task check-ins. Use at the end of an autonomous run, or whenever the user's whole view of the work is a single summary. Covers decisions taken on their behalf, assumptions, unverified claims, and new rules awaiting ratification.
---

# Handover checklist

Write `plans/HANDOVER.md`. This is the user's **entire** view of a run they did not
watch. Write it for someone deciding whether to trust the result, not for someone
admiring it.

## The test for what goes in

> If they read only this file and approved, what would they later wish they had known?

That is the content. Everything else is noise. A checklist that lists what went right is
a status report; one that surfaces what a reviewer would want to challenge is a handover.

## Sections

**Decisions taken on your behalf.** Every fork where you chose instead of asking. State
the choice, the alternative, and the reason in one line each. If you followed
documentation, cite it. If you chose the conservative option because research was
inconclusive, say that plainly — it flags the shakiest ground in the run.

**Assumptions.** Things you took as true without confirming. Each one is a place the work
breaks if you were wrong, so it is worth more space than the parts that went well.

**Not verified.** Anything asserted but not observed: tests that were written but not run
against failing code, behaviour confirmed only by unit test and never live, claims that
depend on a version or environment you could not probe. Distinguish *tested* from
*demonstrated* — they are not the same evidence.

**Awaiting ratification.** New rules, checklists or blueprints you wrote. You authored
them; the user has not agreed to them. List each with its file, what it asserts, and its
enforcement tier. Ratified items move to `.ai/10-ratification-archive/`.

**Manual steps.** Anything you could not do — user-level settings, credentials,
infrastructure — with enough detail that it can be done without re-reading the task.

**What broke and what it cost.** Mistakes made during the run, whether they were caught,
and whether they are already in `docs/RETROSPECTIVE.md`. Omitting these is the single
easiest way to make a handover misleading, and the reviewer usually finds them anyway.

## Rules

- **Be specific.** "Updated the docs" tells a reviewer nothing. Name the file and the
  claim that changed.
- **Never pad.** If a section is empty, write "none" and move on. A handover padded to
  look thorough trains the reader to skim, and skimming is how the one item that mattered
  gets missed.
- **Report failures plainly.** If tests fail, say so with the output. If a step was
  skipped, say which and why. Reporting a partial result as complete is worse than the
  partial result.
- **Link, don't restate.** Point at the ledger entry, the commit, the decision record.
  This file is an index into the evidence, not a copy of it.

Keep it scannable — a reviewer should reach the risky parts in under a minute. The
checklist is the deliverable of an unattended run; if it is wrong, nothing else in the
run can be trusted either.
