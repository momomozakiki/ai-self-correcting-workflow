# Planning — golden rules (risk, reversibility, verification)

Status: drafted by orchestrator 2026-08-30, unreviewed
Applies when a plan is being written or reviewed, before any code exists. The problem
statement, acceptance criteria and recorded rationale are in `problem-and-requirements.md`.

**How to work these.** They are questions, not prescriptions — do not convert them. Work them
against the **plan**, never against the plan's own summary. Report every answer, including the
ones that pass. Where the plan simply does not address an item, **that is the finding**, not a
reason to skip the item.

Reversibility is decided at planning time. After the change it is a fact, not a choice.

## Always

- [ ] Does the plan touch anything **irreversible** — published history, the ledger,
      credentials? Stop and check it against the Tier-0 prohibitions before planning further.
- [ ] If this plan is **abandoned halfway**, is the system left in a working state? — if not,
      reorder the steps so each one lands complete.

Sources: ISO 31000:2018; NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 (2016).

## When the change touches shared or persistent state

- [ ] Is the **rollback path stated, and has it been performed** rather than assumed? — write
      the rollback command and run it once against a scratch copy.
- [ ] What is the **blast radius** if this is wrong — who or what is affected beyond the change
      itself? List the downstream consumers; if the list is unknown, that is the finding.
- [ ] Can this be delivered as a **smaller reversible increment first**? — split off the part
      that can be shipped and undone independently.

Sources: *Site Reliability Engineering* (Beyer et al., O'Reilly, 2016); ISO 31000:2018.

## When the change is exposed to untrusted input or external systems

- [ ] Has **"what can go wrong" been asked explicitly**, not only "what are we building"? —
      spend one pass listing failure modes before listing steps.
- [ ] Are the risks that were **identified and knowingly accepted** written down, not just the
      mitigated ones? Record the accepted risk and who accepted it.

Sources: Threat Modeling Manifesto (2020); ISO 31000:2018.

## Always, when deciding how the work will be shown to be done

- [ ] Is the way this will be verified decided **before the work starts**, rather than after? —
      verification designed afterwards tends to verify what was built, not what was wanted.
- [ ] **Can the proposed check actually fail** — has it been run against the unfixed state? Run
      it before the fix and record the failure.
- [ ] Does **anything other than the author's assertion** confirm the work is done? Name the
      independent signal: a test, a reviewer, a measurement.
- [ ] Is *"did we do a good enough job"* **scheduled as a step**, rather than left to memory? —
      add the retrospective to the plan's closing phase.
- [ ] Does the check's **scope actually include the thing it is being cited for** — would it
      pass identically if that thing were absent? A check that cannot fail on your subject is
      not evidence about your subject, however green it is.
- [ ] Is every count and measurement in the plan **reproducible by a command**, or was it
      arrived at by reading and summing? — commit the command, not the number; a figure nobody
      can re-derive is an assertion wearing the costume of a measurement.

Sources: IEEE 1012-2024, *Standard for System, Software, and Hardware Verification and
Validation*; Threat Modeling Manifesto (2020). The last two items are promoted from this
repository's own record on 2026-08-30, both past the two-occurrence threshold in `GROWTH.md`.
**Scope:** `--self-test` printed `checklist sources validated` over an empty directory
(2026-08-29); it now reports 88 items while 119 exist, because it globs one of two folders;
and `[ ok ] every doc carries frontmatter` was cited as evidence about `golden-rules/`, which
that check has never walked. **Counts:** the golden-rules migration plan has been wrong about
its own arithmetic three times — "9 ×" summing to 19, "13 added" when it was 16, and "8 group
conditions" when there were 11 — each caught only because something recounted independently.

## When the plan has more than a handful of criteria

- [ ] Does verification cover **the acceptance criteria**, or only the parts that were easy to
      test? — map each criterion to the check that settles it; the unmapped ones are the gap.
- [ ] Is there a check for **the failure this plan is meant to prevent**, not only for the
      feature it adds? Add the regression case that reproduces the original failure.

Sources: IEEE 1012-2024; *Site Reliability Engineering* (Beyer et al., O'Reilly, 2016).
