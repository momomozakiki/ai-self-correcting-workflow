# Checklist report — planning/risk-and-verification.md

Golden: golden-rules/planning/risk-and-verification.md
Status: drafted by orchestrator 2026-08-30, unreviewed
Worked: 2026-08-31 against plans/golden-rules-migration.md

- pass | Does the plan touch anything **irreversible** — published history, the ledger, credentials? Stop and check it against the Tier-0 prohibitions before planning further. | Asked and answered in stage 3: "Do not touch history/2026-W28.md or history/2026-W32.md — history/ is a Tier-0 protected path; the guard will deny it and corrections go by appending."
- pass | If this plan is **abandoned halfway**, is the system left in a working state? — if not, reorder the steps so each one lands complete. | Three declared stopping points, each described as a state where the repo is coherent and shippable. This is the plan's strongest structural property.
- finding | Is the **rollback path stated, and has it been performed** rather than assumed? — write the rollback command and run it once against a scratch copy. | No rollback path is stated anywhere in the plan. Stage 1's archive of `.ai/` into plans/archive/ is a de-facto one, but it is not named as such, no command is written, and none has been run. Stage 3 does `rm -r .ai/`.
- pass | What is the **blast radius** if this is wrong — who or what is affected beyond the change itself? List the downstream consumers; if the list is unknown, that is the finding. | Stage 3 item 6 maps it file by file — CLAUDE.md lines, four skills, GUIDE §13, the layout auditor, the adopter fragment.
- pass | Can this be delivered as a **smaller reversible increment first**? — split off the part that can be shipped and undone independently. | Seven stages with a gate between each, and stage 1 explicitly valuable alone.
- pass | Has **"what can go wrong" been asked explicitly**, not only "what are we building"? — spend one pass listing failure modes before listing steps. | Stage 6 carries "The predicted failure, so you know what to look for"; stage 4 carries "If the guard does not fire, stop."
- finding | Are the risks that were **identified and knowingly accepted** written down, not just the mitigated ones? Record the accepted risk and who accepted it. | The risks are written down well (RetiredMachinery is "a floor, not a proof"; the fabrication and avoidance holes). **Who accepted them is never named.** Every disclosure is authored by the agent proposing the work.
- pass | Is the way this will be verified decided **before the work starts**, rather than after? — verification designed afterwards tends to verify what was built, not what was wanted. | Each stage's gate is written in the same commit as the stage, before the work.
- pass | **Can the proposed check actually fail** — has it been run against the unfixed state? Run it before the fix and record the failure. | Repeatedly and deliberately: gate 0 required the auditor to refuse a false claim before being trusted; test_golden_rules was proven by planting a malformed file; these report tests by planting a report with a line added and one removed.
- pass | Does **anything other than the author's assertion** confirm the work is done? Name the independent signal: a test, a reviewer, a measurement. | The stage-gate auditor, read-only and separate. It has refused four times and found five things in gate 2.
- finding | Is *"did we do a good enough job"* **scheduled as a step**, rather than left to memory? — add the retrospective to the plan's closing phase. | The gates are scheduled; a retrospective is not. Nothing in the plan schedules an entry in docs/RETROSPECTIVE.md at any stage's close, and the two-occurrence promotion threshold in GROWTH.md depends entirely on that file being written.
- finding | Does the check's **scope actually include the thing it is being cited for** — would it pass identically if that thing were absent? A check that cannot fail on your subject is not evidence about your subject, however green it is. | Fires on the plan itself. Gate 3 cites `--self-test`'s "checklist sources validated" line as evidence about the library, but `run_self_test` globs `05-domains/` only (workflow_hook.py:1560), so it covers 88 of 119 items and would report identically if all 31 planning items vanished.
- finding | Is every count and measurement in the plan **reproducible by a command**, or was it arrived at by reading and summing? — commit the command, not the number; a figure nobody can re-derive is an assertion wearing the costume of a measurement. | Partly. `scripts/test_id_diff.py` is committed and re-derives the test-ID diff. But the selection figures (9/50/88/88, the seven contexts) and the degeneracy figures (104 of 119, 50 of 119) were produced by **scripts left in a scratch directory and never committed**, so nobody else can re-derive them. The item that was promoted to catch exactly this has caught its own author.
- pass | Does verification cover **the acceptance criteria**, or only the parts that were easy to test? — map each criterion to the check that settles it; the unmapped ones are the gap. | Each gate criterion names the command that settles it, and gates 4–6 say plainly where the answer is a reading rather than a run.
- pass | Is there a check for **the failure this plan is meant to prevent**, not only for the feature it adds? Add the regression case that reproduces the original failure. | `RetiredMachinery` reproduces all three recorded stale-claim incidents and is asserted to catch 3/3.

## Working notes

- **Acted on during the trial:** the two uncommitted measurement scripts found by the
  "reproducible by a command" item were moved into `scripts/` and committed, which is what
  that item exists to force. The finding stays recorded as a finding rather than being
  retro-marked `pass`, because it was true when the checklist was worked.
- Two items — "who accepted the risk" and "schedule the retrospective" — are about
  *accountability at closure* rather than about risk itself. If they recur in a later report
  they are a promotion candidate for a closure-focused group, per GROWTH.md's depth route.
- The rollback finding has an obvious cheap fix (name the archive as the rollback path and
  actually restore it once into a scratch copy) that is out of scope here and belongs to
  stage 3, which is the stage that does the deleting.
- No item was unanswerable and none was `n/a`. On this plan, all fifteen applied.
