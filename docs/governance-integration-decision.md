---
title: Governance Integration Decision Record (v14 → workflow-core)
version: 1.0
last_validated: 2026-08-04
official: true
source: agent-generated
tags: [governance, decision-record, adr, enforcement, provenance, v14]
applies_when: "Deciding whether a governance control from the v14 framework is enforced here, and why; or re-checking the runtime assumptions behind that decision."
estimated_tokens: 2400
---

# Governance Integration Decision Record
**Version 1.0** — *Which v14 controls this repository enforces, which it merely follows, and which it only records.*

## Revision History
| Version | Date       | Change   |
|---------|------------|----------|
| 1.0     | 2026-08-04 | Initial. Dispositions all 24 sections of the imported v14 framework against the real runtime; records the source-verification results and the runtime assumptions they rest on. |

---

## 1. Why this record exists

The [Self-Growing Checklist Ecosystem v14](self-growing-checklist-ecosystem/index.md) was
imported as an external reference framework. It is written for an enterprise fleet of agents
with API access, cryptographic identity infrastructure, and a vector store. This repository is
one developer running Claude Code against a Claude Pro subscription.

Adopting it verbatim would produce artifacts that *look* enforced and are not. This record
fixes that by assigning every control one of three tiers, and by writing the tier into the
artifact itself so no future reader has to guess.

| Tier | Meaning | How you can tell |
|------|---------|------------------|
| **live** | A hook, test, or schema enforces it. Breaking it produces a visible signal. | Named in `hooks/workflow_hook.py` or `tests/test_hook.py` |
| **convention** | The agent is expected to follow it; nothing blocks. | Named in `SKILL.md` or a ledger/rule field |
| **declarative** | Recorded for portability only. Not enforceable in this runtime. | Carries `enforcement_status: declarative` and a reason |

**The rule: no artifact may imply enforcement it does not have.** A declarative field is
written as `null` with its reason attached, never as a plausible-looking fake value.

## 2. Runtime assumptions

Verified against official sources on 2026-08-04. These are the facts the tiering rests on; if
they change, re-run this table before trusting the dispositions.

| Fact | Source |
|------|--------|
| Pro is $20/mo ($17 annual) and **includes Claude Code** | [claude.com/pricing](https://claude.com/pricing) |
| Claude Code authenticates with the subscription login. A set `ANTHROPIC_API_KEY` **overrides it** — *"Claude Code will use this API key for authentication instead of your Claude subscription"* | [support 11145838](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan) |
| Sonnet 5 is the default model. Opus 5 is *"the new default model on Claude Max, and the strongest model on Claude Pro"* | [Opus 5 announcement](https://www.anthropic.com/news/claude-opus-5) |
| **On Pro, Fable 5 runs on pay-as-you-go usage credits** — not covered by plan limits. Max and premium seats get up to 50% of weekly limits on Fable at no extra cost; the promotion extending that to others ended 2026-07-19 | [support 15424964](https://support.claude.com/en/articles/15424964-claude-fable-5-on-your-plan) |
| On the Anthropic API, `opus` → **Opus 5** and `sonnet` → Sonnet 5 — but this **requires Claude Code v2.1.219+**; before that, `opus` resolved to Opus 4.8. `best` → Fable 5 *"where your organization has access to it"* | [model-config](https://code.claude.com/docs/en/model-config) |
| Usage runs on a rolling 5-hour session window plus weekly caps, with a **separate weekly cap for Opus**, shared with the Claude app | [costs](https://code.claude.com/docs/en/costs), [support 9797557](https://support.claude.com/en/articles/9797557-usage-limit-best-practices) |

### What follows from them

- **No API key ⇒ no vector search, no embeddings, no LLM-judge grader.** v14's RAG metrics
  (grounding confidence, attribution completeness, policy-aligned action score) and its semantic
  retrieval cannot run. Retrieval here is manifest-keyword lookup, which is what Claude Code
  Skills already do.
- **One local agent ⇒ no counterparty.** Cryptographic identity, delegation, and shadow-AI
  detection all presuppose a second party to authenticate to, delegate to, or detect. There
  isn't one.
- **Quota is finite and Opus is metered separately ⇒ model choice is a cost control.** Stay on
  Sonnet 5 for routine work; `/model opus` for hard passes. **Fable 5 is a paid escalation on
  Pro and must never be a shipped default** — not in a skill, not in a subagent's frontmatter,
  not in an `ANTHROPIC_DEFAULT_*` variable.
- **An `ANTHROPIC_API_KEY` in the environment silently moves billing off the subscription.**
  The hook warns about this at `SessionStart` and in `--self-test`. Warning only: API-key auth
  is a legitimate choice, just rarely the intended one here.

## 3. Source verification

v14 cites heavily. Spot-checking the load-bearing claims:

| Claim in v14 | Verdict |
|--------------|---------|
| CISA / Five Eyes *Careful Adoption of Agentic AI Services* (2026-05-01), five risk categories | **Confirmed.** Real joint publication; five categories confirmed. Secondary summaries word the last two inconsistently ("structural brittleness" vs "structural cascading failures"), so this repo keys its ledger field on stable slugs — `privilege`, `design`, `behavioral`, `structural`, `accountability` — which survive any rewording. |
| Clawdentity, Agent Identity Protocol (AIP), Agent Passport System (APS) as IETF work | **Confirmed real, but overstated.** All three are *individual Internet-Drafts*, not adopted standards. v14 §23 scores "IETF RFCs" at authority 10; **Internet-Drafts rate 7–8** and should be cited as working documents. |
| APS's seven constraint dimensions (scope, spend, depth, time, reputation, values, reversibility) | **Confirmed.** |
| `did:trail` as a W3C DID method for autonomous agents | **Not independently verified.** Recorded as unverified. It sits in the declarative tier regardless, so nothing here depends on it. |
| "82% of organizations discovered unknown AI agents" (§20) | **Not verified.** Attributed to a survey; treat as unsourced until checked. Does not affect any tiering decision. |

## 4. Section-by-section disposition

| v14 § | Control | Tier | Reason |
|-------|---------|------|--------|
| 1–3 | Vision, five pillars, three-tier architecture | convention | Framing. Already compatible with GUIDE §1. |
| 4 | 21-step Master Execution Checklist | convention | Adopted as a **mapping**, not a renumbering — see GUIDE §12. Phase 0–3 stays canonical. |
| 5 | Chunked library + manifests | live (structure) / convention (use) | The `.ai/` tree exists and `--self-test` checks parts of it. Retrieval is manifest-keyword; **the RAG/vector layer is dropped** (no API key). |
| 6 | Enforcement tiers (ABSOLUTE/MANDATORY/CONDITIONAL/OPTIONAL) | convention | Maps onto this repo's existing fixed-invariant vs conditional-trigger split. |
| 7 | Hierarchical inheritance | convention | Applies to rule files in `.ai/`; nothing enforces override precedence. |
| 8 | Component blueprints | convention | Seeded empty. Grows per retrospective. |
| 9 | Selection engine | convention | Project-type detection is agent judgment. |
| 9.3 | Unified evaluation metrics (ARS/RGC/ACR/PAAS) | **dropped** | Requires an LLM judge and a vector store. Not implementable without an API key. Recorded here rather than in the library, so nothing dangles. |
| 10 | Path-dependent policy evaluation | convention | The weekly ledger already records decisions and rationale; a second path log would duplicate it. |
| 11 | Five-risk taxonomy | **live** | The five slugs are a documented ledger field (`history/FORMAT.md`) and a `risk_source` on every rule file. |
| 11 | Structural risk specifically | declarative | Requires a second agent. No multi-agent composition here. |
| 12.1 | Dual-validation gate | convention | Technical gate = lint/tests (Phase 2); human gate = the user. |
| 12.2 | Sandboxed execution | declarative | The real local mechanism is Claude Code permission modes plus `PreToolUse` hooks, not a staging environment. Recorded so an adopter with infrastructure can wire it up. |
| 12.3 | Governance-in-the-Loop | convention | Accurate description of what hooks already do. |
| 13 | HITL ratification + confidence calibration | convention | Ratification is the user approving a plan. **Calibration numerics are declarative** — nothing scores confidence. |
| 14 | Retrospective + growth protocols | **live** | `docs/RETROSPECTIVE.md`; `--self-test` reports recurring entries. |
| 15.1 | Five behavioral metrics (MirrorDNA) | declarative | Needs per-session scoring infrastructure that doesn't exist here. |
| 15.2 | Self-hardening loop | **live** | A mistake recurring twice becomes a SKILL.md checklist item and a rule file. |
| 15.3 | Cross-session risk composition | convention | A ledger field, not a computed budget — computing it would require scoring every action. |
| 15.4 | Agent loop detection | **live** | Implemented in `handle_post_tool_use`; advisory, never blocking. |
| 16.1–16.2 | Autonomy flywheel, adoption metrics | convention | Descriptive. |
| 16.3 | Governance maturity levels 1–5 | **live** | Computed by `--self-test`, written to `maturity-tracker.json`. Reported, never enforced. |
| 17 | Operational guardrails | mixed | Research budget, git-divergence halt, secret redaction: **live/convention**. Financial-impact caps and risk budgets: declarative. |
| 17.3 | Reversibility requirement | **live** | Git is the rollback mechanism; the Stop hook's dirty-tree breadcrumb already enforces the checkpoint discipline. |
| 18.1–18.2 | Declarative governance manifest | declarative | `governance.yaml` exists for adopters and is **not parsed by any hook here** (stdlib-only: no PyYAML). Machine-read files are JSON. |
| 18.3 | Natural-language policy compilation | convention | "Turn this sentence into a rule file" is a thing the agent does on request. |
| 19.1 | DIDs, SPIFFE, Ed25519 identity + log signing | declarative | Single operator, subscription auth, no key infrastructure. Fields present and `null`. |
| 19.2–19.4 | Trust profiles, lineage, agent cards | declarative | No certification body, no fleet. |
| 19.6 | Delegation framework + APS constraint dimensions | declarative | No second agent to delegate to. The seven APS dimensions are recorded for adopters. |
| 20 | Shadow AI detection | declarative | Meaningless for a single operator on their own machine. |
| 21 | Success metrics & KPIs | mixed | The ones `--self-test` can compute are live; the RAG-derived ones are dropped (see §9.3). |
| 22 | File templates | live | Instantiated under `.ai/` and `templates/ai-library/`. |
| 23 | Source authority scoring | convention | Adopted **with a correction**: Internet-Drafts score 7–8, not 10 (see §3). |
| 24 | Final mandate | convention | Reads as intent, not as an enforceable rule set. |

## 5. What was dropped outright

Not merely declarative — removed, because carrying the artifact would imply a capability that
cannot exist here:

- **RAG grounding / attribution / policy-alignment metrics (§9.3, parts of §21).** No embeddings,
  no retrieval scoring, no judge model without API access.
- **Vector-search fallback in the loading strategy (§5.4 step 5).** Manifest lookup only.

## 6. Re-checking this record

Re-verify §2 whenever the Claude Code CLI or the plan's model lineup changes — the `opus` alias
resolution and Fable's billing status have both already moved once. Re-run
`python hooks/workflow_hook.py --self-test` after any change to the library or config; it reports
the current maturity level and the checks behind it.
