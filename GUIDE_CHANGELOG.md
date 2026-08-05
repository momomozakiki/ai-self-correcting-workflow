---
title: GUIDE Changelog
version: 1.0
last_validated: 2026-08-05
official: false
source: agent-generated
tags: [changelog, episodic, audit]
applies_when: "Never load — episodic doc history for humans and audit only."
exclude_from_ai: true
estimated_tokens: 700
---

# GUIDE.md — Full Revision History

The relocated Revision History for [`GUIDE.md`](GUIDE.md), per its own §6.3: once the
in-file table passes ~8 rows, history rivals the content it documents, so the full
record moves here and the live doc keeps only the latest ≤3 rows plus a link.

Named `GUIDE_CHANGELOG.md` rather than `CHANGELOG.md` because `GUIDE.md` sits at the
repository root, where a bare `CHANGELOG.md` would read as the *project's* changelog.
This file holds one document's history and nothing else. Append-only: newest row on
top, old rows are never rewritten.

| Version | Date       | Change |
|---------|------------|--------|
| 5.4     | 2026-08-05 | Plan review. Every rule in `05-domains/` answers "against the code in question", and `rule-task-checklist` told the agent to produce a plan checklist while supplying nothing to interrogate it with — so a plan was reviewed by nothing, structurally: code review measures code *against* the plan and cannot see a defect *in* it. §13 gains `.ai/03-planning/` — 5 categories, 31 items, answered at Phase 1, sourced to ISO/IEC/IEEE 29148:2018, 42010:2022, IEEE 1012-**2024** (1012-2016 is superseded), ISO 31000:2018, INCOSE SEH 5th ed., NASA/SP-2016-6105 Rev 2, the Google SRE book, the Threat Modeling Manifesto and Nygard's ADR. Never gated on tech stack. The selection table moves from `05-domains/manifest.json` to `.ai/00-system/checklist-selection.json` and gains a `workflow_phase` axis, so one table serves both folders — a breaking path change for adopters who vendored the library earlier. Trialled against its own plan: ten of thirty-one items found something, including an unstated rollback, a missing out-of-scope list, and the unnamed assumption that a plan reviewed by its own author is worth anything. |
| 5.3     | 2026-08-05 | The checklist system lands. §13 gains ten sourced review categories in `.ai/05-domains/` (80 items), each citing a document with an authority tier and a `confidence_level` **derived** by `derive_confidence` rather than asserted; conditional loading is defined once as manifest data and read by both skills. §7.3: the Stop hook no longer counts its own auto-breadcrumb as uncommitted work — writing it had guaranteed the next Stop would fire again, forever. §7.4: `--self-test` reports which gate blocked the maturity climb and what passes above it, instead of a bare floor that hid six passing checks behind one warn. New `documentation_exclude` config key and `exclude_from_ai` frontmatter support, closing the ROADMAP backlog item. New `docs/checklist-system.md` consolidates the two adopted source documents and records the five citation defects found in them. |
| 5.2     | 2026-08-05 | §7.3: the Stop flags gain a modification-time fallback against `session_start_ts`, because `PostToolUse` sees only `Edit\|Write\|MultiEdit` and both failure directions showed up in practice — a ledger appended by a shell redirect nagged anyway, and a source file rewritten by `sed -i` would not have nagged at all. Records why `FileChanged` was evaluated and rejected. §13: `live` now distinguishes `deny` from `ask` strength via a tested `enforcement_mode` field, after an `ask` was waved through and the rule it guarded was broken anyway. |
| 5.1     | 2026-08-05 | New §7.5: why the Tier-0 guard is a `PreToolUse` hook rather than a `permissions.deny` rule, and why it emits both `deny` and `ask`. §7.1/§7.3 gain the `PreToolUse` event and the fail-open consequence; §13 records the four re-tierings. Revision History folded here per §6.3. |
| 5.0     | 2026-08-04 | Governance integration (MAJOR — three new sections). §4 gains loop detection, reversibility and a Tier-0 line; new §12 maps the imported 21-step SOP onto Phase 0–3; new §13 documents the `.ai/` governance library; new §14 records the runtime assumptions (Claude Pro + Claude Code, no API key) that the tiering rests on. |
| 4.7     | 2026-08-04 | New §7.4: `main_branch` resolution order (explicit pin → local `refs/remotes/<remote>/HEAD` autodetect → opt-in `git remote show` probe → `main`), plus the `main_branch_detected` state key in §7.2. Adds `stop_hook.main_branch_autodetect` / `main_branch_remote` / `main_branch_probe_remote`. |
| 4.6     | 2026-07-18 | §4 Phase-3 commit step: standardized on `git commit -m` and cautioned against heredocs / `-F -` (Bash-safety-layer rejection) and a bare `git commit` (editor hang). Mirrored in `hooks/workflow_hook.py`, `docs/claude-code-hook-integration.md`, and `SKILL.md`. |
| 4.5     | 2026-07-18 | §6.3/§6.5: clarified `last_validated` semantics — it records the last **content** review, not the last edit. A mechanical/frontmatter-only edit bumps `version` + adds a history row but leaves `last_validated` unchanged. Resolves an internal contradiction; mirrored in `DOC_TEMPLATE.md` + `SKILL.md`. |
| 4.4     | 2026-07-11 | §6.4: added a pointer to the Progressive Disclosure Guide's new §3.1 (optional distributed `SCOPE.md` scaling tier) and §5.1 (content-quality rules), harvested from an incoming AI-documentation guide. |
| 4.3     | 2026-07-10 | §6.3/§6.4: added the lazy **doc-folding** convention — bound the in-file Revision History (~8 rows / ≤3 kept) and relocate full history to a sibling Episodic `CHANGELOG.md` (`exclude_from_ai: true`). Renamed §6.4 to "Folding a document into a folder". |
| 4.2     | 2026-07-10 | §6 recast as the unified Documentation Standard (frontmatter provenance + versioning + Progressive Disclosure splitting); added this frontmatter/Revision History. |
| 4.1     | (prior)    | Centralized, configurable, self‑improving baseline (pre‑frontmatter). |
