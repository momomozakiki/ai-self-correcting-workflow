---
title: Governance library (workflow-core)
version: 1.0
last_validated: 2026-08-04
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

| Tier | Meaning |
|------|---------|
| **live** | A hook or test enforces it. Breaking it produces a visible signal. |
| **convention** | The agent follows it; nothing blocks. |
| **declarative** | Recorded for portability. Not enforceable here; written as `null` with a reason, never faked. |

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
artifact, in the artifact where the format allows it.

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
