---
title: Self-Growing Checklist Ecosystem (AI Agent Governance Framework)
version: 14.0
last_validated: 2026-08-04
official: false
source: user-provided, origin unknown
tags: [governance, agentic-ai, checklist, reference, v14, imported]
applies_when: "Instantiating or auditing the governance library; deciding whether a proposed control is live, convention, or declarative."
estimated_tokens: 900
---

# Self-Growing Checklist Ecosystem
**Version 14.0** — *Imported reference framework for AI agent governance, folded per GUIDE §6.4.*

## Revision History
| Version | Date       | Change |
|---------|------------|--------|
| 14.0    | 2026-08-04 | Folded into this folder from two flat files (v13 + v14, 3,054 lines, ~96% duplicated). v13 retired; the v13→v14 delta moved to [`CHANGELOG.md`](CHANGELOG.md). Split into five children, each inside the ≤5,000-token Semantic budget. Frontmatter added — the flat files carried none. |

---

## What this is

An externally-authored governance framework for AI coding agents: a 21-step master
checklist, a chunked rule library, enforcement tiers, risk taxonomy, HITL ratification,
behavioral metrics, autonomy tiers, and an agent registry with cryptographic identity.

**It is not the operating rules of this repository.** `GUIDE.md` is. This framework is
source material that has been dispositioned control-by-control against what can actually
be enforced by a Claude Code session on a Claude Pro subscription with no API key.

➡️ **Read [`../governance-integration-decision.md`](../governance-integration-decision.md)
first.** It records which parts of this framework are:

| Tier | Meaning |
|------|---------|
| **live** | A hook or test enforces it. Breaking it produces a visible signal. |
| **convention** | The agent follows it; nothing blocks. Recorded in the ledger or a rule file. |
| **declarative** | Recorded for portability only — not enforceable in this runtime, and labelled as such wherever it appears. |

## Provenance

Agent-generated content supplied by the user; origin unverified, so `official: false`.
Its own citations were spot-checked during integration — the CISA/Five Eyes five-risk
framework is real, and Clawdentity / AIP / APS are real IETF documents but **individual
Internet-Drafts, not adopted standards**, which the framework's own source-authority scale
(§23 in [`05-reference.md`](05-reference.md)) overstates. See the decision record for the
full verification table.

## Children

| File | Covers | Read it when |
|------|--------|--------------|
| [`01-foundations.md`](01-foundations.md) | Foreword, §1–4 | You need the problem statement, five pillars, three governance tiers, or the 21-step checklist |
| [`02-library-architecture.md`](02-library-architecture.md) | §5–10 | You're laying out the rule library, choosing an enforcement tier, or applying inheritance and blueprints |
| [`03-risk-gates-and-metrics.md`](03-risk-gates-and-metrics.md) | §11–15 | You're classifying risk, designing a gate, running HITL ratification, or working on metrics and loop detection |
| [`04-autonomy-and-governance.md`](04-autonomy-and-governance.md) | §16–20 | You're setting autonomy tiers, writing guardrails, or working with the agent registry |
| [`05-reference.md`](05-reference.md) | §21–24 | You need a KPI target, a config template, the source-authority scale, or the final mandate |
| [`CHANGELOG.md`](CHANGELOG.md) | v13 → v14 delta | Never loaded — `exclude_from_ai: true` |

## How this maps onto the workflow

The 21 steps are **not** adopted as a replacement numbering. `GUIDE.md` §12 holds the
mapping table from each v14 step to its Phase 0–3 home, with the enforcement tier attached.
Phase 0–3 remains canonical.
