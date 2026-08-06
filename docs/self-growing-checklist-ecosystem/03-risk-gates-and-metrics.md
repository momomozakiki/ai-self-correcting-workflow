---
title: Risk taxonomy, validation gates, and behavioral metrics
version: 14.0
last_validated: 2026-08-04
official: false
source: user-provided, origin unknown
parent: index.md
tags: [governance, agentic-ai, checklist, reference, v14]
applies_when: "Classifying a risk, designing a validation gate, running the HITL ratification handover, or working with behavioral metrics, self-hardening, and loop detection."
estimated_tokens: 2813
---

# Risk taxonomy, validation gates, and behavioral metrics

*Part of the [Self-Growing Checklist Ecosystem v14.0](index.md).*

> **Enforcement note.** This is an imported reference framework, not the operating rules of
> this repository. Which parts are actually enforced here — and which are convention or purely
> declarative — is recorded in [`../governance-integration-decision.md`](../governance-integration-decision.md).
> Read that first; treat everything below as the source material it dispositions.

---

# 11. The Forking & Mutation Protocol with Expanded Risk Taxonomy

## 11.1 Forking a Domain Rule File
1. **Find Base**: Identify the closest existing folder.
2. **Mutate**: Remove irrelevant rules, add new rules, upgrade/downgrade enforcement.
3. **Save**: Save as `09-variants/task-[name]-v1/`.
4. **Apply & Ratify**: Apply to current task. Propose merging useful changes back to main library.

## 11.2 Forking a Component Blueprint
1. **Find Base**: Select the closest existing blueprint.
2. **Mutate**: Remove/add fields, change mutable variables.
3. **Generate Variant**: Save as new blueprint in `09-variants/`.

## 11.3 Expanded Risk Taxonomy (CISA Five-Risk Framework)

| Risk Source | Definition | Examples | Risk Weight Range | Controls |
| :--- | :--- | :--- | :--- | :--- |
| **Component Risks** | Vulnerabilities in tools, APIs, or data sources | Unsanitized API inputs, insecure data storage | 1-3 | Security validation, dependency scanning |
| **Design Risks** | Flaws in planning, reasoning, or action logic | Insufficient validation, missing rollback | 4-6 | Checklist validation, path auditing |
| **Capability Risks** | Risks from autonomous action execution | Unauthorized access, unintended side effects | 7-10 | Bounded autonomy, approval gates |
| **Structural Risks** (NEW) | Risks from composition and interaction of multiple agents | Conflicting priorities, cascading failures, Agent A undoing Agent B's work | 6-9 | Agent coordination protocol, shared state management, dependency graph validation |
| **Accountability Risks** (NEW) | Unclear or diffused responsibility | No named owner, shared ownership without clear authority, no audit trail | 8-10 | Named owner requirement, audit trails with cryptographic signatures, regular accountability reviews |

**Implementation**: Every new rule file must include a `risk_source` and `risk_weight` field:

```json
{
  "id": "rule-smart-contract-validation",
  "rule": "MUST validate smart contract signatures.",
  "enforcement": "MANDATORY",
  "risk_source": "design",
  "risk_weight": 7,
  "risk_justification": "Prevents execution of unauthorized transactions"
}
```

For multi-agent interactions:

```json
{
  "id": "rule-coordination-protocol",
  "rule": "All agents MUST follow the coordination protocol for shared state access.",
  "enforcement": "MANDATORY",
  "risk_source": "structural",
  "risk_weight": 8,
  "risk_justification": "Prevents conflicting agent actions from corrupting shared state"
}
```

---

# 12. The Dual-Validation Gate & Governance-in-the-Loop

## 12.1 The Dual-Validation Gate

| Gate | Validator | Timing | Blocks What? |
| :--- | :--- | :--- | :--- |
| **Gate 1: Technical** | AI + CI/CD | Steps 11-16 | Blocks `git commit` |
| **Gate 2: Human/UX** | Human (PM/Designer) | Steps 19-20 | Blocks `git merge` |

## 12.2 Sandboxed Execution for Escalation

When an agent action is escalated to human review, the action must be executed in a sandboxed environment that:
- **Isolates** the action from production systems
- **Logs** all side effects for human review
- **Requires explicit approval** before promotion to production
- **Provides rollback capability** if approved action causes issues

```json
{
  "sandboxed_execution": {
    "enabled": true,
    "environment": "staging_isolated",
    "requires_approval": true,
    "log_retention": "90d",
    "rollback_required": true
  }
}
```

## 12.3 Governance-in-the-Loop: Beyond Human-in-the-Loop

While Human-in-the-Loop (HITL) provides checkpoints for human review, it is insufficient for agents operating at machine speed. Our framework implements **Governance-in-the-Loop**—where governance is embedded in the agent's runtime loop through:

- **Behavioral metrics** that continuously measure agent integrity
- **Self-hardening** that converts mistakes into permanent rules
- **Cross-session risk** that accumulates across sessions
- **Reversibility** that enables rollback of any action
- **Loop detection** that halts infinite cycles
- **Structural risk monitoring** for multi-agent interactions
- **Accountability tracking** with cryptographic audit trails

This ensures governance is not a checkpoint but a continuous, embedded property of the agent's operation.

---

# 13. The Ratification Handover (HITL) with Confidence Calibration & Correction Logging

## 13.1 What the AI Always Does (No Human Needed)
- Executes all **MANDATORY** rules.
- Executes all **CONDITIONAL** rules that evaluate to `true`.
- Applies proven component blueprints.
- Writes the full code, writes unit tests, commits, and pushes.

## 13.2 What the AI Asks the Human (The Ratification Checklist)

| # | Tag | Category | Example |
| :--- | :--- | :--- | :--- |
| 1 | 🧠 | **New Domain Rule File** | "I created `blockchain/rule-smart-contract-validation.json`." |
| 2 | 🧠 | **New Blueprint** | "I forked `login/basic.blueprint` into `login-passwordless.blueprint`." |
| 3 | 🎨 | **UX/Color** | "I set the primary button to #1A73E8. Does this match the brand?" |
| 4 | 📝 | **Copy/Content** | "The error message is 'Invalid credentials.' Is this acceptable?" |
| 5 | 🔮 | **Ambiguity** | "I set the session timeout to 15 minutes. Confirm?" |
| 6 | ⚖️ | **Principle Override** | "I bypassed DRY in the hot loop for performance." |

**Human Time**: < 2 minutes.

## 13.3 Confidence Calibration Protocol

| Element | Description |
| :--- | :--- |
| **Confidence Score** | AI's self-assessed confidence (0-100%) recorded for every decision point. |
| **Calibration History** | Comparison of confidence scores against actual human validation outcomes. |
| **Calibration Adjustment** | If AI consistently overestimates confidence, scores are recalibrated downward. |
| **HITL Trigger Threshold** | If Adjusted Confidence < 85%, generate ratification item automatically. |

## 13.4 Correction-as-Training-Signal Logging

Every human correction triggers structured logging in `10-ratification-archive/[task]/corrections.jsonl`:

```json
{
  "correction_id": "CORR-2026-08-04-001",
  "session_id": "2026-08-04-task-001",
  "agent_id": "agent-alpha-01",
  "checklist_item": "CHECK 2",
  "ai_original": "Set session timeout to 15 minutes.",
  "human_correction": "Set session timeout to 30 minutes for enterprise users.",
  "root_cause": "AI assumed standard user base, but project is enterprise.",
  "confidence_before": 92,
  "confidence_after": 78,
  "rule_update": "Added rule-timeout-context.json to 05-domains/security-auth/",
  "provenance": {
    "previous_correction": null,
    "overwrote_correction": null
  },
  "timestamp": "2026-08-04T14:30:00Z"
}
```

---

# 14. The Retrospective & Self-Improvement Loop with Governance Failure Mode Checks

## 14.1 The Retrospective Checklist

| # | Question | Action if "Yes" |
| :--- | :--- | :--- |
| 1 | Did I violate a MANDATORY rule? | Strengthen the rule's AI Action prompt. |
| 2 | Did I spend > 30 minutes researching? | Pre-seed a new Domain folder. |
| 3 | Did I encounter an edge-case not covered? | **Add a new rule file** to the relevant folder. |
| 4 | Did the human correct a UI/Color choice? | Update the Component Blueprint. |
| 5 | Did the human approve a new Security rule? | Move from `09-variants/` to permanent location. |
| 6 | Did my confidence calibration deviate? | Update calibration history. |
| 7 | Did I encounter a Tier 0 violation? | **Immediately escalate to security officer.** |
| 8 | Did my cross-session risk accumulate? | Review and adjust autonomy if needed. |
| 9 | Did I encounter conflicting corrections from different humans? | Flag for governance review. Update the affected rule file with clarification. |
| 10 | Did a confident error (high confidence, wrong outcome) occur? | Calibrate confidence scores downward for similar future tasks. |
| 11 | Did a human correction silently overwrite a previous correction? | Escalate to ensure proper provenance. |
| 12 | Did any Unified Evaluation metric fall below target? | Investigate root cause. Update RAG retrieval strategy or policy definitions. |
| 13 | **NEW: Was a structural risk detected in multi-agent interactions?** | Add coordination protocol rules. |
| 14 | **NEW: Was an accountability gap identified?** | Assign named owner and update registry. |
| 15 | **NEW: Was a loop detected and halted?** | Analyze root cause and add loop prevention rules. |

## 14.2 The Three Library Growth Protocols
1. **20a – Adding New Domain Folders (Breadth):** Permanently save new folders to `05-domains/`.
2. **20b – Improving Existing Folders (Depth):** Add new rule files to existing folders.
3. **20c – Refining Component Blueprints:** Update mutable variables based on human corrections.

## 14.3 Folder Manifest Update Protocol
Whenever a new rule file is added to a folder, the AI **must** update the folder's `manifest.json`.

---

# 15. Behavioral Governance Metrics, Self-Hardening & Cross-Session Risk Composition

## 15.1 The Five Behavioral Metrics (MirrorDNA Protocol)

| Metric | Definition | Target |
| :--- | :--- | :--- |
| **Integrity Index** | Composite score from gate violations, read:write ratio, recurring patterns | ≥ 80 |
| **Drift Coefficient** | Variation of session quality scores across sessions | ≤ 0.15 |
| **Recurrence Rate** | Fraction of documented mistakes that recur across sessions | ≤ 0.20 |
| **Verification Ratio** | Reads / (reads + writes) | ≥ 0.67 |
| **Stability Half-Life** | Average sessions before a recurring pattern is resolved | ≤ 1.5 sessions |

## 15.2 The Self-Hardening Loop

```
1. A mistake occurs during execution
   ↓
2. Documented in `08-behavioral-metrics/self_critique.jsonl`
   ↓
3. If the same mistake recurs in ≥2 sessions → marked as "recurring"
   ↓
4. If recurring in ≥2 sessions → becomes a mandatory gate rule
   ↓
5. Gate violations penalize the Integrity Index
   ↓
6. If Integrity Index < 70 → trigger autonomy reduction
   ↓
7. The mistake is permanently codified as a new rule file
```

## 15.3 Cross-Session Risk Composition

```json
{
  "cross_session_risk": {
    "enabled": true,
    "rolling_window_sessions": 10,
    "time_decay_factor": 0.95,
    "cumulative_risk_budget": 100,
    "escalation_threshold": 80
  }
}
```

| Action Type | Risk Weight |
| :--- | :--- |
| Reading public data | 1 |
| Reading internal data | 3 |
| Writing non-critical data | 5 |
| Writing financial/payment data | 8 |
| Modifying infrastructure | 10 |
| Multi-agent structural actions (NEW) | 7-9 |
| Actions with unclear accountability (NEW) | 9-10 |

## 15.4 Agent Loop Detection (NEW)

The AI MUST monitor for loop conditions:

| Loop Type | Detection Criteria | Action |
| :--- | :--- | :--- |
| **Step Repetition** | Same action repeated >3 times without progress | **HALT**, log to `loop_detection.jsonl`, escalate |
| **Tool Retry** | Same failed tool called >3 times | **HALT**, log to `loop_detection.jsonl`, escalate |
| **No Progress** | No measurable progress toward goal for >5 minutes | **HALT**, log to `loop_detection.jsonl`, escalate |

**Implementation**:

```json
{
  "loop_detection": {
    "enabled": true,
    "step_repetition_threshold": 3,
    "tool_retry_threshold": 3,
    "no_progress_timeout": 300,
    "escalation": "human",
    "logging": "08-behavioral-metrics/loop_detection.jsonl"
  }
}
```

---
