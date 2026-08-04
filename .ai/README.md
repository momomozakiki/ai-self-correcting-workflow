---
title: Governance library (workflow-core)
version: 1.2
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
00-system/              config, registry, autonomy boundaries, maturity tracker
01-phases/              one rule file per workflow step (Phase 0-3 + v14 step mapping)
02-market-rules/        immutable golden rules; prohibitions/ is tier 0
05-domains/             technology rules      - empty, grows per retrospective
06-components/          blueprints            - empty, grows per retrospective
08-behavioral-metrics/  hook-written JSONL + what is deliberately absent
09-variants/            forks awaiting ratification
10-ratification-archive/ HITL decision history
GROWTH.md               how the library grows, and the self-hardening rule
```

## Provenance convention

`00-system/` config files carry `.prov.md` sidecars per GUIDE section 6.2. Rule files under
`01-phases/` and `02-market-rules/` do **not** - they embed a `provenance` block in the JSON
itself, which the sidecar convention exists to substitute for. One provenance record per
artifact, in the artifact where the format allows it. `RuleSchema.test_provenance_is_populated`
holds every rule and prohibition to this.

## Hand-maintained from here

This tree was bootstrapped once by a throwaway generator; it is **not** regenerated.
Rules are added by hand as retrospectives produce them (see `GROWTH.md`), and a
regenerator would clobber exactly that accumulated knowledge. The one generated file
is `00-system/maturity-tracker.json`.

## Regenerating the maturity tracker

```bash
python hooks/workflow_hook.py --self-test
```

Reports the health checks and the derived maturity level (1-5), and rewrites
`00-system/maturity-tracker.json`. The level is reported, never enforced.
