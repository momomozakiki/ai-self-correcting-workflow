# Checklist report — planning/problem-and-requirements.md

Golden: golden-rules/planning/problem-and-requirements.md
Status: drafted by orchestrator 2026-08-30, unreviewed
Worked: 2026-08-31 against plans/golden-rules-migration.md

- pass | Is the problem stated **separately from the proposed solution**? — the test is whether the first paragraph would still be true if a different solution were chosen. | The Context section describes `.ai/` drift in its own terms — eleven metadata fields, a manifest bump, a mirror, a GUIDE row, a 959-line test file — and stays true whatever replaces it.
- pass | Is there evidence the problem is **real** — a measurement, a report, a failure — rather than an anticipation? Name the observation; if there is none, say the problem is anticipated. | Concrete and countable: the per-item cost is enumerated, and docs/RETROSPECTIVE.md carries the drift incidents.
- finding | Is it stated **who is affected**, and how they would notice if this succeeded? | Never stated. The plan does not say whether the sufferer is the single operator, a future session, or an adopter vendoring workflow-core — and those three want different things. The adopter question surfaced only when the gate auditor raised it at gate 2, which is late.
- pass | Is the problem statement free of a **presumed cause** that has not been demonstrated? — separate the symptom from the suspected cause, and verify the cause before planning around it. | The claim that schema weight caused the drift is backed by the recorded incidents rather than asserted.
- pass | Does the plan name the **assumption that, if wrong, would invalidate it** — and say how you would find out early that it was wrong? | Several, with the discovery method attached: the design review's "not simpler, merely relocated"; concurrency being undocumented, hence serial dispatch in v1; gate 4's "if the guard does not fire, stop."
- finding | Is the **cost of doing nothing** stated, so the work can be declined on evidence rather than on preference? | Absent. The plan argues the library is expensive but never says what it costs to leave it alone, so the work cannot be declined on evidence. Stopping Point A is argued on what is *gained* by stopping, which is a different question.
- finding | Does the plan say what it will **deliberately not do**? — an unbounded plan cannot be finished. | Per-stage only ("no agents, no deletions" at stage 2). There is no global out-of-scope list, and the absence shows: `templates/` distribution of golden-rules/ was neither in scope nor explicitly out of it, so it went unnoticed until the auditor asked.
- pass | Was **"do nothing" considered as an option**? State why the status quo was rejected, not only why the change is good. | Three declared stopping points, each a legitimate outcome, and the summary table compares complexity against today at each one.
- pass | Were the **criteria for choosing stated before the choice**, or only after it? — write the criteria first, then score the options against them. | Three independent reviews ran before the rewrite was committed to, and their corrections are carried in the plan.
- pass | Is **at least one rejected alternative recorded**, with the property that ruled it out? — a decision without a recorded rejected alternative is indistinguishable from a decision never made. | The first draft's self-improving loop, rejected because it rebuilt confidence self-adjustment; the inverted strike criterion, rejected and corrected.
- pass | Is the decision recorded somewhere **durable**, with its date and context? — an ADR is the cheap form: context, decision, consequences. | The plan is dated and version-controlled, and every decision has a matching ledger entry in history/.
- pass | Is each criterion **verifiable** — is the observation that settles it stated? A command, an output, a state. | Each gate names the command that settles it, and gates 4–6 say where the answer is a reading rather than a run.
- finding | Does each criterion state **one thing**, or is it two joined by "and"? — a compound criterion cannot be half-passed. | Gate 1 criterion 1 is two: the suite passes **and** every removed ID has a recorded reason. It was half-passed exactly that way — the suite was green while the removal list was wrong twice about its own arithmetic. Gate 3's first criterion has the same shape.
- finding | Could **two readers reach different conclusions** about whether it is satisfied? — replace the subjective term with the measurement you would actually take. | Gate 6 is explicitly "judged by reading" and asks whether output is "vague or aspirational". The subjectivity is disclosed rather than hidden, which is the right handling, but the answer to the question as asked is still yes.
- pass | Is each criterion **necessary** — would removing it change the outcome? Delete it and see whether the plan still describes the same result. | Each gate criterion has bitten at least once, or is the sole check on its property.
- pass | Does the plan specify **behaviour where behaviour would do**, rather than implementation? — state the observable outcome and let the implementation be chosen later. | Gates describe observable outcomes. Stage 3 names exact line numbers, which is implementation — appropriate for a migration whose whole risk is missing an edit site.
- pass | Is each criterion **feasible** within the stated constraints and time? — name the constraint it strains, or move it to a later increment. | Each was met as written, except where amended in the open with the amendment recorded.
- finding | Can each criterion be **traced back to the problem statement** it serves? — drop the criterion, or add the problem it answers. | Stages 4–7 do not trace to the stated problem. The plan says so itself — *"Everything from stage 2 on is capability, not cleanup"* — which means the problem statement justifies stages 0–3 and the remaining four stages are answering a question the plan never posed.

## Working notes

- **The sharpest finding is the last one**, and the plan convicts itself in its own words. The
  stated problem is that `.ai/` grew too heavy. Stages 4–7 build agents and an orchestrator,
  which does not make anything lighter. That is not an argument against building them — it is
  an argument that the plan needs a **second** problem statement for the capability half, or
  the traceability question has no good answer at stages 4–7.
- Three findings cluster on the same absence: no stated stakeholder, no cost of inaction, no
  global out-of-scope list. All three are *framing* rather than *risk*, and all three would
  have been cheap to write at Phase 1 and are expensive to retrofit now. If this cluster
  recurs on another plan it is a promotion candidate.
- The compound-criterion finding is the one with a demonstrated cost: Gate 1 criterion 1 was
  half-passed exactly as the item predicts, and the half that failed was the half nobody was
  counting.
- No item was `n/a` and none was unanswerable. All eighteen applied to this plan.
- **Trial result across both reports: 12 findings from 33 items.** For comparison, the plan
  records `.ai/03-planning/` returning 10 findings on its own author when first trialled.
