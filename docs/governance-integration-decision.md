---
title: Governance Integration Decision Record (v14 → workflow-core)
version: 1.2
last_validated: 2026-08-05
official: true
source: agent-generated
tags: [governance, decision-record, adr, enforcement, provenance, v14]
applies_when: "Deciding whether a governance control from the v14 framework is enforced here, and why; or re-checking the runtime assumptions behind that decision."
estimated_tokens: 2400
---

# Governance Integration Decision Record
**Version 1.1** — *Which v14 controls this repository enforces, which it merely follows, and which it only records.*

## Revision History
| Version | Date       | Change   |
|---------|------------|----------|
| 1.0     | 2026-08-04 | Initial. Dispositions all 24 sections of the imported v14 framework against the real runtime; records the source-verification results and the runtime assumptions they rest on. |
| 1.1     | 2026-08-05 | Audit of v1.0's own tier claims (see §6). Two re-tiers: step 1 git sync **live → convention**, step 10 documentation standard **convention → live**. Seven risk-taxonomy violations and one false v14 step mapping corrected. `tests/test_governance_library.py` added so the tier claims in this record are now checked rather than asserted. |
| 1.2     | 2026-08-05 | New §8: enforcing the Tier-0 prohibitions with a `PreToolUse` guard, and why `permissions.deny` lost to it. Three prohibitions and `rule-no-heredoc-stdin` move **convention → live**; `prohibition-commit-secrets` deliberately does not. Old §8 renumbered to §9. |

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
| 11 | Five-risk taxonomy | **live** | `risk_source` on every rule file, enforced by `RiskTaxonomy` in `tests/test_governance_library.py`. *(v1.0 called this live while nothing checked it; seven artifacts had drifted — see §6.)* The ledger's `**Risk:**` field in `history/FORMAT.md` is a **separate, frozen** five-slug list, not this taxonomy; v1.0 conflated the two. |
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

## 6. Audit of v1.0's own claims (2026-08-04)

v1.0 asserted a tier for every control but shipped nothing that could check one. An audit
one commit later found the library had already drifted from this record in five ways, none
of which any test or hook would ever have surfaced:

| Finding | Correction |
|---|---|
| `rule-loop-detection` used `risk_source: "behavioral"`, absent from the §11.3 taxonomy | → `capability`; runaway autonomous execution is capability risk |
| Six artifacts carried a `risk_weight` outside their source's band | Sources corrected where mislabelled (`doc-standard`, `living-docs`, `unfinished-plan` → `design`); genuine deviations kept at their honest weight and given a `risk_weight_note`. **No weight was changed to fit a band** — see §7 |
| `.ai/GROWTH.md` documented `privilege` and `behavioral`, inventing two sources and dropping `component` and `capability` | Corrected to the CISA five, with the weight bands added (their absence is why the weights drifted unnoticed) |
| Eight rules claimed `live` with no way to name the enforcing code, and two blocks in `autonomy-boundaries.json` did the same | Every `live` artifact now carries `enforced_by`, resolved against real functions and tests |
| `rule-no-heredoc-stdin` claimed v14 step 12, which GUIDE §12 tiers as live, while the rule is convention | `maps_to_v14_step: null` with a reason: it was self-hardened locally and has no v14 ancestor |

Two tier claims in §4 were wrong and are corrected here:

- **Step 1, git sync: live → convention.** The hook *reports* branch, dirty state and
  ahead/behind counts. Nothing runs `git fetch && git pull --rebase`, and nothing stops a
  session on a dirty tree. Reporting a condition is not enforcing a response to it.
- **Step 10, documentation standard: convention → live.** An under-claim in the other
  direction: `run_self_test` really does check every doc for frontmatter, and
  `TestSelfTest::test_reports_missing_frontmatter` really does cover it.

## 7. Why no weight was retuned

The first draft of the fix proposed nudging three `risk_weight` values so they would clear
their imported bands. That is the same failure as a faked `live` tier wearing different
clothes: an honest number bent until it satisfies a check. The bands in §11.3 were written
for an agent fleet, and some of them do not transfer to a single-operator repository —
a missing audit trail means something different when there is one operator and git already
records who changed what.

So the escape hatch is a written argument, not a new number. `risk_weight_note` records why
the imported band does not fit, and `RiskTaxonomy.test_risk_weight_is_in_band_or_carries_a_note`
accepts an out-of-band weight only when one is present. It also rejects a note on an
in-band weight, so the field cannot become boilerplate.

## 8. Enforcing the Tier-0 prohibitions (2026-08-05)

§4's row for v14 §12.2 already named the real local mechanism: *"Claude Code permission
modes plus `PreToolUse` hooks."* Until now nothing used it, so all four Tier-0
prohibitions sat at `convention`. Three moved to `live`. The choice of mechanism is the
part worth recording, because the obvious answer was wrong.

**`permissions.deny` is the stronger tool, and it does not fit.** Deny is evaluated
before ask and allow, applies in every permission mode including `bypassPermissions`,
and a `PreToolUse` hook returning `"allow"` cannot loosen it — for anything a pattern
can express, a deny rule beats a hook. Three properties of *these* prohibitions defeat
it:

1. **Patterns anchor on a literal prefix.** `Bash(git push --force*)` misses
   `git push origin main --force` and `git push -f`. The official docs carry an explicit
   warning that patterns constraining command *arguments* are fragile, with near-identical
   examples.
2. **A deny rule carries no exceptions.** One broad enough to stop a force-push to `main`
   also stops the same push to a topic branch you own. The prohibition is *never
   force-push a **shared** branch* — and shared-ness is a fact about the repository, not
   about the command string.
3. **Two shells.** `Bash(...)` and `PowerShell(...)` are separate namespaces. On Windows a
   Bash-only rule list is bypassed by the tool the agent reaches for first.

Several candidate patterns were also simply dead. One spanned a pipe, which the matcher
splits into independently-checked subcommands, so it could never have matched anything —
a rule that reads like enforcement and is not. That is the failure mode §6 was written
about, and it nearly recurred here in a different costume.

**So: a parser, emitting two decisions.** `deny` where the command plus the repository
settle the question — the destination branch is protected, the deletion target is inside
the audit trail. `ask` where they do not: whether a commit is already published, or
whether a particular heredoc is the dangerous kind, is not visible in the command.
Denying every candidate would block legitimate work; guessing would be worse. An `ask`
still enforces — the call cannot proceed without a human — while a false positive costs
one keystroke.

That distinction is what made the guard buildable at all. `rule-no-heredoc-stdin` v1.0
had declined a hook because *"the false-positive cost on legitimate heredocs was judged
higher than the failure it prevents"*, and `ROADMAP.md` had deferred the whole question
over the same false-positive risk. Both were weighing a hard block. `ask` inverts the
trade, and the rule moved to `live` with it.

**`prohibition-commit-secrets` did not move, and that is the load-bearing decision here.**
The guard sees the command, not the file contents being committed, so `git commit` of a
file containing a key is invisible to it — the guard could only ever catch a secret typed
inline. Shipping that as `live` would have made three real controls and one piece of
theatre indistinguishable. Real coverage means scanning `git diff --cached`, which is a
new false-positive surface of its own; it is queued on the roadmap. Until then the tier
says `convention` and the note says why.

**What `live` does not mean here.** The dispatcher is fail-soft, so an exception in a
guard allows the call. Subcommand splitting ignores quotes, so a separator inside a quoted
string yields an extra fragment (over-reporting — the safe direction). In `dontAsk` mode an
`ask` becomes a silent block rather than a prompt. And the guard sees tool calls only,
never a terminal opened outside Claude Code; OS-level enforcement is the sandbox's job,
which is why §4's row for v14 §12.2 stays `declarative`. Every re-tiered artifact repeats
these limits in its own `enforcement_note`, because a tier that overstates itself is
exactly what this record exists to prevent.

`SettingsWiring` in `tests/test_governance_library.py` closes the last gap: `enforced_by`
can prove `guard_force_push` exists, but not that Claude Code ever calls it. That depends
on a hook entry in `.claude/settings.json` — a file no other test read. Delete the entry
and the guard would become unreachable code while every tier claim still resolved.

## 9. Re-checking this record

Re-verify §2 whenever the Claude Code CLI or the plan's model lineup changes — the `opus` alias
resolution and Fable's billing status have both already moved once. Re-run
`python hooks/workflow_hook.py --self-test` after any change to the library or config; it reports
the current maturity level and the checks behind it.
