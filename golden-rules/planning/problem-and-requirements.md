# Planning — golden rules (problem, requirements, rationale)

Status: drafted by orchestrator 2026-08-30, unreviewed
Applies when a plan is being written or reviewed, before any code exists. What the plan costs
if it is wrong, and how it will be proven done, are in `risk-and-verification.md`.

**How to work these.** They are questions, not prescriptions — do not convert them. Work them
against the **plan**, never against the plan's own summary: the summary is written by the same
author and repeats what is present, while a plan review is looking for what is absent. Report
every answer, including the ones that pass. Where the plan simply does not address an item,
**that is the finding**, not a reason to skip the item.

## Always, before a plan is written

- [ ] Is the problem stated **separately from the proposed solution**? — the test is whether
      the first paragraph would still be true if a different solution were chosen.
- [ ] Is there evidence the problem is **real** — a measurement, a report, a failure — rather
      than an anticipation? Name the observation; if there is none, say the problem is
      anticipated.
- [ ] Is it stated **who is affected**, and how they would notice if this succeeded?
- [ ] Is the problem statement free of a **presumed cause** that has not been demonstrated? —
      separate the symptom from the suspected cause, and verify the cause before planning
      around it.
- [ ] Does the plan name the **assumption that, if wrong, would invalidate it** — and say how
      you would find out early that it was wrong?

Sources: ISO/IEC/IEEE 29148:2018; ISO/IEC/IEEE 42010:2022; ISO 31000:2018; *Site Reliability
Engineering* (Beyer et al., O'Reilly, 2016); INCOSE Systems Engineering Handbook, 5th ed.
(2023).

## When the work is discretionary, **or** when it competes with other work

- [ ] Is the **cost of doing nothing** stated, so the work can be declined on evidence rather
      than on preference?
- [ ] Does the plan say what it will **deliberately not do**? — an unbounded plan cannot be
      finished.
- [ ] Was **"do nothing" considered as an option**? State why the status quo was rejected, not
      only why the change is good.
- [ ] Were the **criteria for choosing stated before the choice**, or only after it? — write
      the criteria first, then score the options against them.

Sources: NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 (2016); INCOSE Systems
Engineering Handbook, 5th ed. (2023).

## When more than one approach was available

- [ ] Is **at least one rejected alternative recorded**, with the property that ruled it out? —
      a decision without a recorded rejected alternative is indistinguishable from a decision
      never made.
- [ ] Is the decision recorded somewhere **durable**, with its date and context? — an ADR is
      the cheap form: context, decision, consequences.

Sources: ISO/IEC/IEEE 42010:2022; M. Nygard, "Documenting Architecture Decisions" (2011).

## Whenever acceptance criteria are written

- [ ] Is each criterion **verifiable** — is the observation that settles it stated? A command,
      an output, a state.
- [ ] Does each criterion state **one thing**, or is it two joined by "and"? — a compound
      criterion cannot be half-passed.
- [ ] Could **two readers reach different conclusions** about whether it is satisfied? —
      replace the subjective term with the measurement you would actually take.
- [ ] Is each criterion **necessary** — would removing it change the outcome? Delete it and see
      whether the plan still describes the same result.
- [ ] Does the plan specify **behaviour where behaviour would do**, rather than implementation?
      — state the observable outcome and let the implementation be chosen later.

Sources: ISO/IEC/IEEE 29148:2018, the characteristics of a well-formed requirement, asked of a
plan's acceptance criteria.

## When the plan is bounded by time or resources, or has more than a handful of criteria

- [ ] Is each criterion **feasible** within the stated constraints and time? — name the
      constraint it strains, or move it to a later increment.
- [ ] Can each criterion be **traced back to the problem statement** it serves? — drop the
      criterion, or add the problem it answers.

Sources: ISO/IEC/IEEE 29148:2018.
