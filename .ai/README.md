---
title: Governance library (workflow-core)
version: 1.3
last_validated: 2026-08-05
official: false
source: agent-generated
tags: [governance, library, enforcement-tiers, index]
applies_when: "Navigating the governance library or checking which tier a control sits in."
estimated_tokens: 500
---

# Governance library (workflow-core)

Instantiation of the Self-Growing Checklist Ecosystem v14, tiered to what this runtime can
actually enforce. **Read [`docs/governance-integration-decision.md`](../docs/governance-integration-decision.md) before trusting anything here** - it records why
each control sits where it does.

## Enforcement tiers

Every artifact declares one:

| Tier | Meaning | Required field |
|------|---------|----------------|
| **live** | A hook or test enforces it. Breaking it produces a visible signal. | `enforced_by`: `path::symbol` references, resolved against the source. Plus `enforcement_mode` (`deny` / `ask`) when a `guard_*` symbol is named — see below |
| **convention** | The agent follows it; nothing blocks. | `enforcement_note`: what is *not* enforced, and what the real mechanism is |
| **declarative** | Recorded for portability. Not enforceable here; written as `null` with a reason, never faked. | `reason`, plus null/empty values |

`tests/test_governance_library.py` checks all three. A `live` tier whose `enforced_by`
names a function that does not exist fails the build, as does a `declarative` block whose
placeholder has been quietly populated. The tiers are claims about code, so they are
tested like claims about code.

### `live` has two strengths

A guard that returns `deny` blocks the call outright. One that returns `ask` blocks it
*until a human answers* — and the answer may be yes. Both produce a visible signal, so
both are `live`; they are not the same promise. Any artifact naming a `guard_*` enforcer
therefore declares an `enforcement_mode` of `deny` or `ask`, and
`tests/test_hook.py::TestEnforcementModeMatchesGuard` feeds the guard a command that must
trip it and asserts the decision it returns equals the declared mode. Declaring `deny` on
a guard that only asks fails the build.

This exists because it happened: the heredoc guard fired correctly, the prompt was
approved, and the rule was broken anyway. An `ask` enforces the prompt, not the outcome.

## Layout

```
00-system/              config, registry, autonomy boundaries,
                        checklist-selection.json - the one table selecting checklists
01-phases/              one rule file per workflow step (Phase 0-3 + v14 step mapping)
02-market-rules/        immutable golden rules; prohibitions/ is tier 0
03-planning/            plan review, Phase 1     - 5 rules, 31 sourced items
05-domains/             code review, Phase 2     - 10 rules, 80 sourced items
06-components/          blueprints               - empty, grows per retrospective
08-behavioral-metrics/  hook-written JSONL + what is deliberately absent
09-variants/            forks awaiting ratification
10-ratification-archive/ HITL decision history
GROWTH.md               how the library grows, and the self-hardening rule
```

## Two review folders, two phases

`03-planning/` reviews the **plan**, before code exists: is the problem stated separately
from the solution, is each acceptance criterion verifiable, what is the rollback, which
alternative was rejected, how will this be proven. `05-domains/` reviews the **code**, once
there is some.

They are separate because `05-domains/` reviews code *against* the plan and so cannot see a
defect *in* the plan — it will confirm that a well-built thing was built well when the thing
should not have been built at all. Before `03-planning/` existed, `rule-task-checklist`
instructed the agent to produce a plan checklist and supplied nothing to interrogate it
with, so a plan was reviewed by nothing.

Which rules load is decided by **one** table, `00-system/checklist-selection.json`, keyed on
`workflow_phase` + `task_size_required` + `tech_stack_required`. It lived inside
`05-domains/manifest.json` until plan rules arrived; a domain manifest cannot be the
authority on a folder it does not contain, and two tables would be two answers.
`ChecklistSelection.test_no_folder_manifest_defines_its_own_selection` stops the second copy
coming back.

## Provenance convention

`00-system/` config files carry `.prov.md` sidecars per GUIDE section 6.2. Rule files under
`01-phases/`, `02-market-rules/`, `03-planning/` and `05-domains/` do **not** - they embed a
`provenance` block in the JSON itself, which the sidecar convention exists to substitute
for. One provenance record per artifact, in the artifact where the format allows it.
`RuleSchema.test_provenance_is_populated` holds every rule and prohibition to this.

## Hand-maintained from here

This tree was bootstrapped once by a throwaway generator; it is **not** regenerated.
Rules are added by hand as retrospectives produce them (see `GROWTH.md`), and a
regenerator would clobber exactly that accumulated knowledge. **Nothing here is
generated.**

## Health check

```bash
python .claude/hooks/workflow_hook.py --self-test
```

Reports the health checks. They are reported, never enforced.

**It writes nothing.** The maturity level (1-5) and `00-system/maturity-tracker.json`
were removed on 2026-08-29: the tracker rewrote a tracked file on every run, so merely
running the suite dirtied the working tree. `test_hook.TestSelfTest.
test_self_test_does_not_write_to_the_repository` now holds the self-test to writing
nothing at all.
