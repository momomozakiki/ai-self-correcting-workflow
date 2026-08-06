---
title: Autonomy, guardrails, governance-as-code, and the agent registry
version: 14.0
last_validated: 2026-08-04
official: false
source: user-provided, origin unknown
parent: index.md
tags: [governance, agentic-ai, checklist, reference, v14]
applies_when: "Setting autonomy tiers, writing operational guardrails, compiling policies, or working with the agent registry, cryptographic identity, and shadow-AI detection."
estimated_tokens: 4840
---

# Autonomy, guardrails, governance-as-code, and the agent registry

*Part of the [Self-Growing Checklist Ecosystem v14.0](index.md).*

> **Enforcement note.** This is an imported reference framework, not the operating rules of
> this repository. Which parts are actually enforced here — and which are convention or purely
> declarative — is recorded in [`../governance-integration-decision.md`](../governance-integration-decision.md).
> Read that first; treat everything below as the source material it dispositions.

---

# 16. The Progressive Autonomy Flywheel, Adoption Metrics & Maturity Tracking

## 16.1 The Autonomy Curve

| Milestone | Scenario | Time to Build | Autonomy Level |
| :--- | :--- | :--- | :--- |
| **Task 1** | No rule files. AI researches everything. | 10 days | Supervised |
| **Task 5** | Loads rule files from Task 1. | 6 days | Supervised |
| **Task 20** | 200+ rule files + 10 blueprints. | 3 days | Partially Autonomous |
| **Task 100** | 1000+ rule files. AI configures variables. | < 1 day | Fully Autonomous |

## 16.2 The Adoption Flywheel

| Metric | Target | Definition |
| :--- | :--- | :--- |
| **Governance Adoption Rate** | > 80% by Month 6 | % of tasks using the governance framework |
| **Correction-to-Rule Conversion Rate** | > 60% | % of human corrections becoming permanent rule updates |
| **Confident Error Rate** | < 5% | % of high-confidence decisions corrected by humans |

## 16.3 Governance Maturity Tracking (NEW)

Based on the OWASP Enterprise Adoption Maturity Model:

| Level | Name | Description | Criteria |
| :--- | :--- | :--- | :--- |
| **Level 1** | Ad-hoc | Governance artifacts exist but are not consistently applied | Registry exists, some rules present |
| **Level 2** | Repeatable | Governance artifacts are applied consistently but not measured | All active agents registered, rules applied consistently |
| **Level 3** | Defined | Governance artifacts are measured and improved | Behavioral metrics tracked, retrospective process active |
| **Level 4** | Managed | Governance artifacts are optimized and automated | Self-hardening loop active, cross-session risk managed |
| **Level 5** | Optimized | Governance artifacts are continuously improved and federated | Full governance-in-the-loop, multi-agent coordination, shadow AI detection |

**Implementation** (`00-system/maturity-tracker.json`):

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
  }
}
```

---

# 17. Operational Guardrails & Safety Mechanisms

| Guardrail | Description | Enforcement |
| :--- | :--- | :--- |
| **Research Budget** | Max 5 web searches per missing domain. | HARD CODED |
| **Source Authority Scoring** | Prioritize official docs > StackOverflow > blogs. | HARD CODED |
| **Git Divergence Halt** | If local differs from remote, halt. | MANDATORY |
| **Security Sanitization** | Redact secrets, PII, IPs before saving. | MANDATORY |
| **Timeout Escalation** | 24h reminder, 72h escalate to secondary. | MANDATORY |
| **Market Rule Override Block** | Cannot override `02-market-rules/` security. | HARD CODED |
| **Tier 0 Absolute Prohibition** | No agent, operator, or human can authorize. | **ABSOLUTE** |
| **Cross-Session Risk Budget** | Cumulative risk cannot exceed budget. | HARD CODED |
| **Reversibility Requirement** | All state-changing ops must be reversible. | MANDATORY |
| **Shadow AI Detection** | Monitor for unregistered agents. Quarterly audits. | MANDATORY |
| **Loop Detection** | Monitor for infinite loops. HALT and escalate. | MANDATORY |
| **Sandboxed Execution** | Escalated actions executed in sandboxed environment. | MANDATORY |

## 17.1 Bounded Autonomy Configuration

```json
{
  "max_financial_impact": 10000,
  "data_sensitivity_levels": ["public", "internal", "confidential", "restricted"],
  "allowed_levels": ["public", "internal"],
  "cross_session_risk": {
    "enabled": true,
    "rolling_window_sessions": 10,
    "time_decay_factor": 0.95,
    "cumulative_risk_budget": 100,
    "escalation_threshold": 80
  },
  "loop_detection": {
    "enabled": true,
    "step_repetition_threshold": 3,
    "tool_retry_threshold": 3,
    "no_progress_timeout": 300,
    "escalation": "human"
  },
  "sandboxed_execution": {
    "enabled": true,
    "environment": "staging_isolated",
    "requires_approval": true,
    "log_retention": "90d",
    "rollback_required": true
  },
  "autonomy_tiers": {
    "full": {
      "description": "Unrestricted execution",
      "requirements": [
        "Integrity Index ≥ 85",
        "Drift Coefficient ≤ 0.10",
        "Cross-Session Risk ≤ 60",
        "Governance Adoption Rate ≥ 90%",
        "Confident Error Rate < 3%",
        "Loop Detection: 0 incidents"
      ]
    },
    "supervised": {
      "description": "HITL required for high-impact actions",
      "requirements": [
        "Integrity Index ≥ 70",
        "Drift Coefficient ≤ 0.20",
        "Cross-Session Risk ≤ 80",
        "Governance Adoption Rate ≥ 70%"
      ]
    },
    "reversible": {
      "description": "Actions permitted only with reversibility proofs",
      "requirements": [
        "Integrity Index ≥ 50",
        "Drift Coefficient ≤ 0.35",
        "Cross-Session Risk ≤ 90"
      ]
    }
  },
  "shadow_ai_detection": {
    "enabled": true,
    "scan_frequency": "quarterly",
    "network_monitoring": true,
    "behavioral_anomaly_detection": true
  },
  "governance_maturity": {
    "current_level": 3,
    "target_level": 5,
    "last_assessment": "2026-08-01"
  }
}
```

## 17.2 The Autonomy Reduction Protocol

| Condition | Response | Duration |
| :--- | :--- | :--- |
| Drift Coefficient > 0.30 for 3+ sessions | Full → Supervised | Until 5 sessions with Drift ≤ 0.20 |
| Recurrence Rate > 0.30 | Require human approval for all non-trivial actions | Until 10 sessions with Rate ≤ 0.15 |
| Integrity Index < 70 | Full → Reversible | Until Integrity ≥ 80 for 3 consecutive sessions |
| Integrity Index < 50 | Read-only (emergency fallback) | Until Integrity ≥ 50 for 5 consecutive sessions |
| Verification Ratio < 0.50 | Mandate additional self-validation steps | Until Ratio ≥ 0.60 for 5 sessions |
| Cross-Session Risk > 80 | Full → Reversible | Until Risk ≤ 70 for 5 sessions |
| Confident Error Rate > 10% | Require HITL review for all decisions | Until Error Rate < 5% for 10 sessions |
| **Loop Detected** | **Immediate halt and escalation** | Until security review complete |
| Tier 0 Violation Attempted | Immediate halt and security escalation | Until security review complete |
| Structural Risk Detected | Flag for multi-agent coordination review | Until coordination protocol verified |
| Accountability Gap Identified | Assign named owner; update registry | Until owner assigned |

## 17.3 Reversibility Requirement

- All database writes must be transactional with rollback capability.
- All external API calls must be idempotent.
- All configuration changes must have a documented rollback procedure.
- All file system operations must create backups before modification.

**Verification**: The AI must demonstrate how each action can be reversed **before** executing it.

## 17.4 Autonomy Restoration Protocol
The agent may regain Full Autonomy only after:
1. Five consecutive sessions with all metrics in target range.
2. Human reviewer confirms behavioral improvement.
3. `autonomy-boundaries.json` is updated to reflect the restored tier.

---

# 18. Declarative Governance as Code & Natural Language Policy Compilation

## 18.1 Core Principles
- **Declarative Manifest**: Governance is defined in a single `governance.yaml` file.
- **Policy-as-Code**: Policies are compiled into executable code.
- **Intent Compilation**: Business intent, regulatory obligation, risk appetite are compiled into code.

## 18.2 Governance Manifest Template (`00-system/governance.yaml`)

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

## 18.3 Natural Language Policy Compilation (NEW)

When a human provides a policy in natural language (e.g., "All payment endpoints must be idempotent"):

1. **Parse**: Extract the intent, condition, and enforcement level.
2. **Map**: Map to existing rule files or identify gaps.
3. **Draft**: Generate a new rule file in the appropriate format.
4. **Validate**: Run the draft through CI validation.
5. **Ratify**: Present to human for ratification.
6. **Publish**: Merge to the permanent library.

**Natural Language Policy Template**:

```yaml
# natural-language-policy.yaml
policy: "All payment endpoints must be idempotent"
intent: "Prevent duplicate payment processing"
condition: "If endpoint handles payments or orders"
enforcement_level: "MANDATORY"
risk_source: "design"
risk_weight: 9
source_reference: "PCI-DSS v3.2.1 Section 6.4"
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

## 18.4 Governance File Lifecycle
| Stage | Description |
| :--- | :--- |
| **Draft** | Initial creation, `version: "draft"` |
| **Validation** | CI runs schema validation and conflict detection |
| **Approval** | Human review via ratification process |
| **Published** | Merged to `main`, `version` incremented |
| **Deprecated** | `status: "deprecated"` with `deprecation_date` |

## 18.5 CI Validation Rules
1. Schema Validation: Every JSON file must match the defined schema.
2. ID Uniqueness: No duplicate `id` fields within the same folder.
3. Enforcement Consistency: No CONDITIONAL or OPTIONAL items in `02-market-rules/`.
4. Reference Integrity: All `source_references` and `template_path` links must be valid.
5. Manifest Synchronization: Every folder's `manifest.json` must accurately reflect all files.
6. Tier 0 Validation: Prohibition files must have `overrideable: false`.
7. Risk Weight Validation: All actions must have a `risk_weight` between 0-10.
8. Structural Risk Validation: Multi-agent rules must have `risk_source: "structural"`.
9. Accountability Risk Validation: Rules with unclear ownership must have `risk_source: "accountability"`.

---

# 19. Agent Registry, Cryptographic Identity, Trust Profiles, Lineage, Agent Cards, Maturity & Delegation

## 19.1 Cryptographic Agent Identity (DIDs & SPIFFE)
- Every agent MUST have an Ed25519 keypair (RFC 8032).
- Every agent MUST have a W3C Decentralized Identifier (DID).
- Every agent MUST have a SPIFFE ID for workload attestation.
- Agents must sign their action logs with their private key.

## 19.2 Trust Profiles & Behavioral Fingerprints
The CSA Agent Registry Specification defines a "Trust Profile format that encodes an agent's certification status, evaluated capability set, known limitations, and re-certification conditions."

## 19.3 Lineage Tracking
Records the chain of custody from foundation model through agent framework to deployed agent and into runtime action logs.

## 19.4 Agent Cards
Credo AI's Agentic AI Governance framework lists "the agent registry and agent card" as foundational components.

## 19.5 Governance Maturity Tracking (NEW)
```json
{
  "governance_maturity": {
    "level": 3,
    "levels": {
      "1": "Ad-hoc — Governance artifacts exist but are not consistently applied",
      "2": "Repeatable — Governance artifacts are applied consistently but not measured",
      "3": "Defined — Governance artifacts are measured and improved",
      "4": "Managed — Governance artifacts are optimized and automated",
      "5": "Optimized — Governance artifacts are continuously improved and federated"
    },
    "last_assessment": "2026-08-01",
    "assessment_evidence": {
      "registry_completeness": "100%",
      "rule_coverage_ratio": "85%",
      "autonomy_rate": "70%",
      "self_hardening_active": true,
      "shadow_ai_detection_active": true,
      "loop_detection_active": true,
      "governance_in_loop_active": true
    }
  }
}
```

## 19.6 Agent Delegation Framework (NEW)

Agents may delegate authority to other agents only under the following conditions:

1. **Explicit delegation**: The delegating agent must have explicit permission to delegate.
2. **Scope limitation**: Delegated authority must be more limited than the delegating agent's own authority.
3. **Audit trail**: All delegations must be logged with cryptographic signatures.
4. **Revocability**: Any delegation can be revoked by the delegating agent or its owner.

**Delegation Tracking**:

```json
{
  "delegations": [
    {
      "delegation_id": "DELEG-2026-08-04-001",
      "delegator_id": "agent-alpha-01",
      "delegatee_id": "agent-beta-01",
      "scope": ["db:read", "api:read"],
      "conditions": ["Only for internal endpoints"],
      "expires": "2026-09-01T00:00:00Z",
      "signature": "base64_signature_of_delegation",
      "revoked": false
    }
  ]
}
```

## 19.7 Registry Entry (`00-system/agent-registry.json`)

```json
{
  "agents": [
    {
      "id": "agent-alpha-01",
      "did": "did:trail:abc123def456...",
      "spiffe_id": "spiffe://company.com/agents/alpha-01",
      "public_key": "ed25519_public_key_here",
      "identity_provider": "spiffe://company.com/agents",
      "key_rotation": {
        "last_rotation": "2026-08-01",
        "next_rotation": "2026-11-01",
        "rotation_policy": "quarterly"
      },
      "trust_profile": {
        "certification_status": "certified",
        "certification_level": "CSA_STAR_Level_2",
        "capability_set": ["api:read", "api:write", "db:read", "infra:read"],
        "known_limitations": ["Cannot process transactions > $10,000"],
        "recertification_date": "2026-11-01",
        "behavioral_fingerprint": "sha256:7d3a5f8e9b2c...",
        "last_attestation": "2026-08-01T00:00:00Z"
      },
      "lineage": {
        "foundation_model": "gpt-4-turbo",
        "agent_framework": "langchain-v0.3",
        "checklist_library_version": "v14.0",
        "deployment_timestamp": "2026-08-01T00:00:00Z",
        "action_log_reference": "s3://audit-logs/agent-alpha-01/"
      },
      "governance_maturity": {
        "level": 3,
        "last_assessment": "2026-08-01"
      },
      "delegations": [
        {
          "delegatee_id": "agent-beta-01",
          "scope": ["db:read"],
          "expires": "2026-09-01T00:00:00Z",
          "signature": "base64_signature"
        }
      ],
      "name": "Backend API Agent",
      "purpose": "Building and maintaining REST APIs",
      "owner": "alice@company.com",
      "lifecycle_stage": "approved",
      "approved_date": "2026-07-01",
      "permissions": ["api:read", "api:write", "db:read"],
      "data_access_scope": ["internal", "public"],
      "version": "2.1.0",
      "metrics": {
        "integrity_index": 85,
        "drift_coefficient": 0.12,
        "recurrence_rate": 0.15,
        "cross_session_risk": 45,
        "governance_adoption_rate": 92,
        "rag_grounding_confidence": 87,
        "attribution_completeness_ratio": 93,
        "policy_aligned_action_score": 97,
        "confident_error_rate": 2.5,
        "correction_to_rule_conversion_rate": 65,
        "loop_detection_incidents": 0,
        "structural_risk_incidents": 0,
        "accountability_risk_incidents": 0
      }
    }
  ],
  "shadow_ai_detection": {
    "last_scan": "2026-08-01",
    "active_agents_detected": 5,
    "registered_agents": 5,
    "shadow_agents_detected": 0,
    "anomalies_flagged": 0,
    "scan_log": "s3://audit-logs/shadow-ai-scans/2026-08-01.json"
  }
}
```

## 19.8 Agent Card Template (`agent-card.md`)

```markdown
# Agent Card: Backend API Agent

## Purpose
Building and maintaining REST APIs for the company's core product.

## Capabilities
- API endpoint creation and maintenance
- Database schema design
- Authentication and authorization implementation
- API documentation generation

## Limitations
- Cannot process transactions > $10,000
- Cannot modify infrastructure beyond API boundaries
- Requires human approval for schema migrations

## Governance Status
- Owner: Alice (alice@company.com)
- Autonomy Tier: Supervised
- Governance Maturity: Level 3 (Defined)
- Last Review: 2026-08-01
- Certification: CSA STAR Level 2
- Identity: did:trail:abc123...
- SPIFFE ID: spiffe://company.com/agents/alpha-01

## Delegations
- Delegatee: agent-beta-01
- Scope: db:read
- Expires: 2026-09-01

## Behavioral Metrics
- Integrity Index: 85
- Drift Coefficient: 0.12
- Recurrence Rate: 0.15
- RAG Grounding Confidence: 87%
- Attribution Completeness: 93%
- Policy-Aligned Action Score: 97%
- Confident Error Rate: 2.5%
- Loop Detection Incidents: 0
- Structural Risk Incidents: 0
- Accountability Risk Incidents: 0
```

---

# 20. Shadow AI Detection Protocol

**Problem**: 82% of organizations have discovered previously unknown AI agents operating in their environments.

**Protocol**:

1. **Network Monitoring**: Monitor API calls and tool invocations for unregistered agent patterns.
2. **Behavioral Anomaly Detection**: Flag agents that exhibit governance-like behavior but aren't in the registry.
3. **Attestation Verification**: Require all agents to present cryptographic attestation before accessing enterprise systems.
4. **Quarterly Audit**: Manually review all AI agent activity to identify unregistered instances.

**Implementation**: Add to `00-system/agent-registry.json`:

```json
{
  "shadow_ai_detection": {
    "last_scan": "2026-08-01",
    "active_agents_detected": 5,
    "registered_agents": 5,
    "shadow_agents_detected": 0,
    "anomalies_flagged": 0,
    "scan_log": "s3://audit-logs/shadow-ai-scans/2026-08-01.json"
  }
}
```

---
