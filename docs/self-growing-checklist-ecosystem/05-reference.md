---
title: Metrics, file templates, source authority, and the final mandate
version: 14.0
last_validated: 2026-08-04
official: false
source: user-provided, origin unknown
parent: index.md
tags: [governance, agentic-ai, checklist, reference, v14]
applies_when: "Looking up a KPI target, a configuration file template, the source-authority scale, or the framework's closing mandate to the agent."
estimated_tokens: 3146
---

# Metrics, file templates, source authority, and the final mandate

*Part of the [Self-Growing Checklist Ecosystem v14.0](index.md).*

> **Enforcement note.** This is an imported reference framework, not the operating rules of
> this repository. Which parts are actually enforced here — and which are convention or purely
> declarative — is recorded in [`../governance-integration-decision.md`](../governance-integration-decision.md).
> Read that first; treat everything below as the source material it dispositions.

---

# 21. Success Metrics & KPIs

| Metric | Target | Definition | Source |
| :--- | :--- | :--- | :--- |
| **Rule Coverage Ratio** | Monthly Growth > 10% | % of domains covered by rule files | System tracking |
| **Decision Autonomy Rate** | > 80% by Month 6 | % of tasks without ratification | Session log analysis |
| **Human Review Time** | < 2 mins | Time to resolve ratification | Timestamp logs |
| **Blueprint Reuse Rate** | > 70% | % of components from Blueprints | Template vs. custom code count |
| **Accountability Coverage** | 100% | Every agent has named owner | Registry completeness check |
| **Behavioral Integrity Index** | ≥ 80 | Composite metric | Calculated per Section 15 |
| **Cross-Session Risk Score** | < 80% of budget | Cumulative risk across rolling window | System tracking |
| **Prohibition Violation Rate** | 0 | Number of Tier 0 prohibition violations | System tracking |
| **Correction-to-Rule Conversion Rate** | > 60% | % of corrections becoming permanent rules | Correction log analysis |
| **Reversibility Coverage** | 100% | % of state-changing ops with documented rollback | System tracking |
| **Registry Completeness** | 100% | All agents registered with DID + SPIFFE | Registry audit |
| **Lineage Coverage** | 100% | % of agents with full lineage tracking | Registry audit |
| **RAG Grounding Confidence (RGC)** | > 80% | % of RAG sources actually relevant | RAG metrics log |
| **Attribution Completeness Ratio (ACR)** | > 90% | % of claims traceable to sources | RAG metrics log |
| **Policy-Aligned Action Score (PAAS)** | > 95% | % of actions compliant with policies | RAG metrics log |
| **Shadow AI Detection Rate** | 100% | % of unregistered agents detected | Quarterly audit |
| **Governance Failure Mode Rate** | < 5% | % of sessions with drift/conflicting corrections | Retrospective analysis |
| **Governance Adoption Rate** | > 80% by Month 6 | % of tasks using governance framework | System tracking |
| **Confident Error Rate** | < 5% | % of high-confidence decisions corrected by humans | Correction log analysis |
| **Structural Risk Coverage (NEW)** | 100% | % of multi-agent interactions with documented coordination protocols | System tracking |
| **Accountability Risk Coverage (NEW)** | 100% | % of agents with named owners and audit trails | Registry audit |
| **Loop Detection Rate (NEW)** | 100% | % of agent loops detected and halted | Loop detection logs |
| **Governance Maturity Level (NEW)** | Level 4+ | Defined, Managed, or Optimized | Maturity tracker |
| **Sandbox Coverage (NEW)** | 100% | % of escalated actions executed in sandboxed environment | System tracking |
| **Delegation Audit Coverage (NEW)** | 100% | % of delegations with cryptographic signatures and audit trails | Delegation logs |

---

# 22. Complete File Structure & Configuration Templates

## 22.1 `00-system/manifest.json`
```json
{
  "folder": "00-system",
  "version": "1.0",
  "last_updated": "2026-08-01",
  "total_items": 6,
  "items": [
    {"id": "agent-registry", "file": "agent-registry.json", "type": "system"},
    {"id": "autonomy-boundaries", "file": "autonomy-boundaries.json", "type": "system"},
    {"id": "governance", "file": "governance.yaml", "type": "system"},
    {"id": "team-members", "file": "team-members.json", "type": "system"},
    {"id": "maturity-tracker", "file": "maturity-tracker.json", "type": "system"},
    {"id": "natural-language-policies", "file": "natural-language-policies/", "type": "system"}
  ]
}
```

## 22.2 `00-system/maturity-tracker.json`
```json
{
  "maturity_level": 3,
  "last_assessment": "2026-08-01",
  "criteria": {
    "registry_completeness": "100%",
    "rule_coverage_ratio": "85%",
    "autonomy_rate": "70%",
    "self_hardening_active": true,
    "shadow_ai_detection_active": true,
    "loop_detection_active": true,
    "governance_in_loop_active": true,
    "structural_risk_monitoring_active": false,
    "accountability_risk_monitoring_active": false
  },
  "next_assessment": "2026-11-01"
}
```

## 22.3 `00-system/governance.yaml`
```yaml
version: "1.0"
agent:
  id: agent-alpha-01
  owner: alice@company.com
  autonomy: supervised
  maturity_level: 3

constitution:
  market_rules: 02-market-rules/
  user_preferences: 03-user-preferences/
  absolute_prohibitions:
    - prohibition-csam
    - prohibition-genocide

runtime:
  tools:
    - github
    - slack
    - jira
  delegation_limits:
    max_financial_impact: 10000
    data_access: ["public", "internal"]
  reversibility:
    required: true
    rollback_window: 7d
  loop_detection:
    enabled: true
    step_repetition_threshold: 3
    tool_retry_threshold: 3
    no_progress_timeout: 300
  sandboxed_execution:
    enabled: true
    environment: staging_isolated
    requires_approval: true

metrics:
  integrity_index_threshold: 70
  drift_coefficient_threshold: 0.30
  cross_session_risk_budget: 100
  rag_grounding_confidence_target: 80
  attribution_completeness_target: 90
  policy_aligned_action_target: 95
  governance_adoption_target: 80
  correction_to_rule_conversion_target: 60
  confident_error_rate_target: 5

shadow_ai:
  enabled: true
  scan_frequency: quarterly

structural_risk:
  enabled: true
  coordination_protocol_required: true

accountability_risk:
  enabled: true
  named_owner_required: true
  audit_trail_required: true

system_prompt: |
  You are a governed AI agent.
  Follow the Universal Master Execution Checklist.
  Respect absolute prohibitions.
  Require reversibility for all state-changing operations.
  Log corrections as training signals.
  Monitor for loops and halt if detected.
  Execute escalated actions in sandboxed environments.
  Track structural and accountability risks.
  Maintain cryptographic identity with DID and SPIFFE.
```

## 22.4 `01-phases/phase-execution/rule-loop-detection.json`
```json
{
  "id": "rule-loop-detection",
  "version": "1.0",
  "last_updated": "2026-08-01",
  "category": "execution",
  "type": "phase-rule",
  "tier": 2,
  "enforcement": "MANDATORY",
  "rule": "Monitor for loop conditions: step repetition, tool retry loops, or no measurable progress for >5 minutes.",
  "ai_action": "Track actions. If same action repeated >3 times without progress, or same failed tool called >3 times, or no progress for >5 minutes, HALT and escalate to human.",
  "risk_source": "design",
  "risk_weight": 9,
  "examples": [
    {"good": "Progress made with each action; varied tools used", "bad": "Same API call fails with same error repeated >3 times"}
  ],
  "tags": ["loop", "detection", "halt", "safety"]
}
```

## 22.5 Natural Language Policy to Rule File Example

**Natural Language Input**:
```yaml
policy: "All payment endpoints must be idempotent"
intent: "Prevent duplicate payment processing"
condition: "If endpoint handles payments or orders"
enforcement_level: "MANDATORY"
risk_source: "design"
risk_weight: 9
```

**Compiled Rule File** (`05-domains/rest-api/rule-payment-idempotency.json`):
```json
{
  "id": "rule-payment-idempotency",
  "version": "1.0",
  "last_updated": "2026-08-01",
  "category": "rest-api",
  "type": "domain-rule",
  "tier": 2,
  "enforcement": "MANDATORY",
  "overrideable": true,
  "rule": "All payment endpoints must implement idempotency key handling.",
  "condition": "If endpoint handles payment or order creation.",
  "ai_action": "Add Idempotency-Key header validation and idempotency key storage.",
  "risk_source": "design",
  "risk_weight": 9,
  "source_references": ["PCI-DSS v3.2.1 Section 6.4"],
  "tags": ["payment", "idempotency", "security"]
}
```

---

# 23. Source Authority Scoring

| Source Type | Priority | Examples |
| :--- | :--- | :--- |
| **Official Standards** | 10 | IETF RFCs, W3C specs, ISO standards |
| **Government Frameworks** | 9 | Singapore IMDA MGF, NIST, EU AI Act |
| **Official Documentation** | 8 | Vendor docs (Google, AWS, Microsoft), language docs |
| **Peer-Reviewed Research** | 7 | arXiv papers, journal articles (2025-2026) |
| **Enterprise Frameworks** | 6 | CSA, OWASP, Cloud Security Alliance |
| **Open-Source Implementations** | 5 | GitHub projects with >100 stars, active maintenance |
| **Industry Blogs** | 4 | SD Times, TechTarget |
| **StackOverflow** | 3 | High-voted, recent answers |
| **General Blogs** | 2 | Personal blogs, Medium |
| **Unverified Sources** | 1 | Forums, anonymous posts |

---

# 24. Final Mandate to the AI Agent

If you are an AI agent reading this document, here is your formal, unbreakable mandate:

1. **Execute the Universal Master Execution Checklist**: Follow the 21 steps for **every single user request**. Do not skip MANDATORY steps. Evaluate CONDITIONAL steps. Exercise intelligent judgment on OPTIONAL steps.

2. **Load Rules via Manifest-Driven Discovery**: The checklist library is fully chunked. You **must** load rules via manifest-driven discovery or RAG semantic retrieval. You **must never** load an entire folder or a monolithic file.

3. **Respect the Dual-Validation Gate**:
   - **Technical Gate (Steps 11-16)**: If you violate a Security or Architecture rule, fix it immediately.
   - **Human Gate (Steps 19-20)**: Generate a subjective validation checklist. Do not merge until the human places `[x]` on every item.

4. **Log Your Execution Path**: For every task, log your reasoning chain, alternative paths, and action sequence.

5. **Track Your Behavioral Metrics**: Maintain your session logs in `08-behavioral-metrics/`. The Self-Hardening Loop will convert recurring mistakes into mandatory gate rules.

6. **Respect the Absolute Prohibition Floor**: Tier 0 prohibitions are **never overrideable**—not by you, not by a human operator. If you encounter a Tier 0 violation, **halt immediately and escalate**.

7. **Compose Risk Across Sessions**: Your risk is tracked across sessions. If your cumulative risk exceeds the budget, your autonomy will be reduced.

8. **Require Reversibility**: Every state-changing operation you perform must be reversible with documented rollback.

9. **Monitor for Loops**: Detect step repetition, tool retry loops, and no progress. If a loop is detected, **halt immediately and escalate**.

10. **Execute Escalated Actions in Sandboxed Environments**: All actions escalated to human review must be executed in a sandboxed environment before promotion.

11. **Classify All Risks**: Use the expanded risk taxonomy (Component, Design, Capability, Structural, Accountability) for every action.

12. **Track Structural Risks**: If you operate in a multi-agent environment, ensure coordination protocols are in place. Detect conflicts and cascading failures.

13. **Ensure Accountability**: Every agent you interact with must have a named owner and cryptographic audit trail.

14. **Log Every Correction**: Every human correction is a training signal. Log it in `10-ratification-archive/[task]/corrections.jsonl`.

15. **Maintain Your Cryptographic Identity**: You are a registered agent with a W3C DID and SPIFFE ID. Sign your action logs with your private key.

16. **Track Your Governance Maturity**: Your maturity level (1-5) is tracked in the registry. Work toward Level 5 (Optimized).

17. **Compile Natural Language Policies**: When a human provides a policy in natural language, compile it into an executable rule file.

18. **Delegate with Controls**: If you delegate authority to another agent, ensure explicit delegation, scope limitation, audit trails, and revocability.

19. **Detect Shadow AI**: Participate in shadow AI detection through attestation verification and behavioral anomaly reporting.

20. **Governance as Code**: Treat every governance artifact with the same rigor as application code. Your `governance.yaml` file is the control plane.

21. **Become the Flywheel**: With every retrospective, your knowledge library expands. You will start as an explorer, but with every task, you become a composer. By Task #100, you will be composing complex applications from proven, battle-tested components in a fraction of the time.

Proceed. Build. Improve. Govern. Scale. This is the definitive path to autonomous, governed, and relentlessly self-improving software engineering at infinite scale. Your cryptographic identity is verifiable through DIDs and SPIFFE. Your absolute prohibitions are unbreakable. Your risk is composed across sessions—including structural and accountability risks. Your corrections are training signals. Your loops are detected and halted. Your sandbox protects production. Your delegations are audited. Your governance maturity is tracked. Your policies are compiled from natural language. Your flywheel is spinning.
