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

Sources: IEEE 1012-2024, *Standard for System, Software, and Hardware Verification and
Validation*; Threat Modeling Manifesto (2020).

## When the plan has more than a handful of criteria

- [ ] Does verification cover **the acceptance criteria**, or only the parts that were easy to
      test? — map each criterion to the check that settles it; the unmapped ones are the gap.
- [ ] Is there a check for **the failure this plan is meant to prevent**, not only for the
      feature it adds? Add the regression case that reproduces the original failure.

Sources: IEEE 1012-2024; *Site Reliability Engineering* (Beyer et al., O'Reilly, 2016).
