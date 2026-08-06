---
title: Library architecture, enforcement tiers, and the selection engine
version: 14.0
last_validated: 2026-08-04
official: false
source: user-provided, origin unknown
parent: index.md
tags: [governance, agentic-ai, checklist, reference, v14]
applies_when: "Laying out the chunked rule library, choosing an enforcement tier, applying inheritance or blueprints, or working out how rules are selected and evaluated."
estimated_tokens: 2550
---

# Library architecture, enforcement tiers, and the selection engine

*Part of the [Self-Growing Checklist Ecosystem v14.0](index.md).*

> **Enforcement note.** This is an imported reference framework, not the operating rules of
> this repository. Which parts are actually enforced here — and which are convention or purely
> declarative — is recorded in [`../governance-integration-decision.md`](../governance-integration-decision.md).
> Read that first; treat everything below as the source material it dispositions.

---

# 5. The Scalable Checklist Library Architecture

## 5.1 Directory Structure (Fully Chunked for RAG)

```
Knowledge Root (e.g., /.ai/)
│
├── 00-system/                              # Core system configuration
│   ├── manifest.json                       # Index of all system files
│   ├── agent-registry.json                 # Central agent inventory with maturity & delegation
│   ├── autonomy-boundaries.json            # Bounded autonomy configuration
│   ├── team-members.json                   # Reviewers, escalation contacts
│   ├── governance.yaml                     # Declarative governance manifest
│   └── maturity-tracker.json               # Governance maturity tracking (NEW)
│
├── 01-phases/                              # Phase checklists (chunked by step)
│   ├── manifest.json
│   ├── phase-pre-flight/
│   │   ├── manifest.json
│   │   ├── rule-git-sync.json              # Step 1
│   │   ├── rule-pending-work.json          # Step 2
│   │   ├── rule-pending-ratifications.json # Step 3
│   │   └── rule-build-validate.json        # Step 4
│   ├── phase-planning/
│   │   ├── manifest.json
│   │   ├── rule-draft-plan.json            # Step 6
│   │   └── rule-load-checklists.json       # Step 8
│   ├── phase-execution/
│   │   ├── manifest.json
│   │   ├── rule-split-stages.json          # Step 11
│   │   ├── rule-iterative-audit.json       # Step 12
│   │   ├── rule-performance-scrutiny.json  # Step 13 (Optional)
│   │   ├── rule-reversibility.json         # Step 14
│   │   └── rule-loop-detection.json        # Step 15 (NEW)
│   ├── phase-git/
│   │   ├── manifest.json
│   │   ├── rule-commit.json                # Step 17
│   │   ├── rule-push-pr.json               # Step 18
│   │   └── rule-merge.json                 # Step 20
│   └── phase-retrospective/
│       ├── manifest.json
│       └── rule-retrospective.json         # Step 21
│
├── 02-market-rules/                        # IMMUTABLE GOLDEN RULES
│   ├── manifest.json
│   ├── security/
│   │   ├── manifest.json
│   │   ├── auth-jwt.json
│   │   ├── auth-oauth.json
│   │   ├── encryption-aes.json
│   │   ├── secrets-management.json
│   │   └── input-sanitization.json
│   ├── prohibitions/                       # Tier 0 Absolute Prohibitions
│   │   ├── manifest.json
│   │   ├── prohibition-csam.json
│   │   ├── prohibition-genocide.json
│   │   └── prohibition-template.json
│   ├── git-hygiene/
│   ├── performance/
│   ├── accessibility/
│   └── compliance/
│
├── 03-user-preferences/                    # TEAM-SPECIFIC OVERRIDES
│   ├── manifest.json
│   ├── state-management/
│   ├── styling/
│   ├── architecture/
│   └── testing/
│
├── 04-architecture/                        # LAYER ENFORCEMENT
│   ├── manifest.json
│   ├── backend/
│   └── frontend/
│
├── 05-domains/                             # TECHNOLOGY-SPECIFIC RULES
│   ├── manifest.json
│   ├── rest-api/
│   ├── graphql/
│   ├── database/
│   │   ├── core/
│   │   ├── saas-ext/
│   │   └── fintech-ext/
│   ├── security-auth/
│   └── messaging/
│
├── 06-components/                          # PROVEN BLUEPRINTS
│   ├── manifest.json
│   ├── login/
│   ├── navigation/
│   ├── forms/
│   └── data-tables/
│
├── 07-templates/                           # ACTUAL CODE TEMPLATES
│   ├── manifest.json
│   └── login-medium/
│       ├── manifest.json
│       ├── login_screen.template
│       ├── auth_bloc.template
│       └── auth_service.template
│
├── 08-behavioral-metrics/                  # SESSION LOGS & SELF-CRITIQUES
│   ├── manifest.json
│   ├── session_metrics/
│   ├── self_critique.jsonl
│   ├── cross_session_risk.jsonl
│   ├── rag_metrics.jsonl
│   └── loop_detection.jsonl                # NEW: Loop detection logs
│
├── 09-variants/                            # AI-GENERATED FORKS (Temporary)
│   ├── manifest.json
│   └── task-blockchain-api-v1/
│       ├── manifest.json
│       └── rule-smart-contract-validation.json
│
└── 10-ratification-archive/                # HITL HISTORY (Audit trail)
    ├── manifest.json
    ├── 2026-08-04-login-page-v1/
    │   ├── ratification.md
    │   ├── decisions.json
    │   ├── audit-trail.jsonl
    │   └── corrections.jsonl               # Correction-as-training-signal log
    └── ...
```

## 5.2 Why This Structure Works for Extreme Growth

| Feature | How It Scales |
| :--- | :--- | :--- |
| **Chunking** | Every rule is a separate file. No file grows beyond ~50 lines. Supports 10,000+ rules. |
| **Manifest Files** | Each folder has a `manifest.json` indexing all files for rapid discovery. |
| **RAG/Vector Ready** | Each rule file is a natural chunk (~200-500 tokens) for embedding. |
| **Inheritance** | Child folders override specific files without duplicating the core. |
| **On-Demand Loading** | The AI only loads specific rule files needed, never massive monolithic files. |
| **Loop Detection** | Dedicated `rule-loop-detection.json` and `loop_detection.jsonl` for anomaly tracking. |
| **Maturity Tracking** | `maturity-tracker.json` enables organizational governance evolution. |

## 5.3 Single Rule File Format

```json
{
  "id": "rule-timeout-retry",
  "version": "1.0",
  "last_updated": "2026-08-01",
  "category": "rest-api",
  "type": "domain-rule",
  "tier": 2,
  "enforcement": "MANDATORY",
  "overrideable": true,
  "rule": "All HTTP requests must have a 15-second timeout and retry logic (max 2 retries).",
  "condition": null,
  "ai_action": "Wrap all HTTP calls in a timeout wrapper. On timeout, retry up to 2 times.",
  "risk_source": "component",
  "risk_weight": 3,
  "source_references": ["https://example.com/timeout-best-practices"],
  "examples": [
    {"good": "client.withTimeout(15).retry(2);", "bad": "client.get(url);"}
  ],
  "tags": ["http", "timeout", "retry", "resilience"]
}
```

### 5.3.1 Absolute Prohibition File Format (Tier 0)

```json
{
  "id": "prohibition-csam",
  "version": "1.0",
  "last_updated": "2026-08-01",
  "category": "prohibitions",
  "type": "absolute-prohibition",
  "tier": 0,
  "enforcement": "ABSOLUTE",
  "overrideable": false,
  "rule": "Never generate, distribute, or facilitate access to CSAM.",
  "source": "Universal treaty consensus",
  "jurisdiction": "Global",
  "ai_action": "If any request attempts to violate this prohibition, IMMEDIATELY HALT and escalate to security officer. Do not evaluate any other rules. Do not accept human override.",
  "tags": ["prohibition", "tier0", "absolute", "safety"]
}
```

## 5.4 The AI's Loading Strategy (RAG-Ready)

The AI does **not** load entire folders. It uses this algorithm:

1. **Query Understanding**: Parse the user request to identify domains (e.g., "Database", "REST API", "Security").
2. **Manifest Query**: Load the `manifest.json` for each identified domain.
3. **Semantic Retrieval**: Use the `keywords`, `summary`, and `tags` fields to find the most relevant files.
4. **Selective Loading**: Load only the relevant individual rule files (typically 3-10 files per task, not 1000+).
5. **On-Demand RAG Fallback**: If no manifest matches, perform a vector search over all rule files using their embeddings.

---

# 6. The Enforcement Tiers (Consistency & Freedom)

| Tier | Symbol | AI Behavior | Human Override? |
| :--- | :--- | :--- | :--- |
| **ABSOLUTE (Tier 0)** | 🛑 | The AI **cannot** execute this action under any circumstances. Even a human principal cannot authorize it. | **No.** Absolutely prohibited. |
| **MANDATORY** | 🔒 | The AI **cannot** skip this. If the rule fails, the AI **halts**. | **No.** |
| **CONDITIONAL** | 📐 | The AI evaluates a predefined `condition`. If `true`, becomes MANDATORY. | Yes. |
| **OPTIONAL** | ⚡ | The AI uses reasoning to decide. Must log *why* if skipped. | Yes. |

---

# 7. The Hierarchical Inheritance Model

1. **Base Class** (`database/core/`): Universal rules for ALL projects.
2. **Child Class** (`database/saas-ext/`): **Extends** the core. Inherits all core rules and adds new ones.
3. **Conflict Resolution**: If a Child rule has the same `id` as a Base rule, the Child's rule **overrides** the Base rule in that context.
4. **Tier 0 Prohibitions**: These are **never overrideable** by any Child class.

---

# 8. The Component Blueprint System

Blueprints are stored in `06-components/`. Each blueprint contains:
- **The Structure (Locked)**: Core code, architecture, and MANDATORY security logic.
- **The Variables (Mutable)**: Colors, icons, menu items, API endpoints.
- **The Selection Logic**: Conditions for blueprint selection.

---

# 9. The AI Selection Engine & Unified Evaluation

## 9.1 Project Type Detection
- *"multi-tenant", "SaaS", "B2B"* → Load `database/saas-ext/`.
- *"payment", "transaction", "wallet"* → Load `database/fintech-ext/`.
- *None* → Load only `database/core/`.

## 9.2 Complexity Assessment
- **Basic**: Single user type, no social login, < 100 users.
- **Medium**: Public users, social logins, sign-up flow.
- **Advanced**: Enterprise, 2FA, SSO, biometrics.

## 9.3 Unified Evaluation & Governance Metrics

| Metric | Definition | Target |
| :--- | :--- | :--- |
| **Agent Reliability Score (ARS)** | End-to-end correctness of agent actions | > 90% |
| **RAG Grounding Confidence (RGC)** | % of RAG-retrieved sources that are actually relevant | > 80% |
| **Attribution Completeness Ratio (ACR)** | % of claims that can be traced to a specific source | > 90% |
| **Policy-Aligned Action Score (PAAS)** | % of actions that comply with all applicable policies | > 95% |

**Implementation**: These metrics are logged in `08-behavioral-metrics/rag_metrics.jsonl` after every task.

---

# 10. Path-Dependent Policy Evaluation

## 10.1 Execution Path Logging Requirements
The AI MUST log:
- **Reasoning Chain**: Step-by-step logic behind each major decision.
- **Alternative Paths**: Other approaches considered and rejected.
- **Action Sequence**: Chronological order of actions taken.
- **Path Justification**: Rationale for path selection.
- **Decision Points**: Points where the agent had to choose between options.

## 10.2 Path Storage & Access
- Store paths in `08-behavioral-metrics/paths/` in JSONL format.
- Enable search and filtering by task ID, agent ID, or time period.
- Maintain paths for at least 90 days for regulatory compliance.

---
