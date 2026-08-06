# Roadmap — Adaptive Self-Correcting Workflow

Planned improvements to the workflow itself. The `SessionStart` hook parses the
first `**Next action:**` line below and surfaces it at session start.

**Next action:** Observe whether `PreCompact` fires before context is discarded; if so, wire it
to `write_unfinished_breadcrumb` so an in-flight plan survives compaction.

---

## Active Epic: Use more of the hook surface

From `docs/hook-event-assessment.md` (2026-08-06). The dispatcher handles 4 of 31 events; these
are the ones worth adding. Each carries a condition that must be **observed, not inferred**, per
`.ai/01-phases/rule-direct-test-disputes.json`.

- [ ] **`PreCompact` → breadcrumb.** `Stop` writes `plans/UNFINISHED.md` on a dirty tree, but a
      long session compacts before it stops, and compaction is what most often loses in-flight
      plan state. Reuses existing idempotent code. *Condition: confirm it fires before context
      is discarded.*
- [ ] **`SessionEnd` → closure check.** Nothing currently verifies the Phase 3 self-check at the
      point it stops being fixable; `Stop` is per-turn and capped at `max_blocks: 2`, so on a
      long session the reminder is spent early and end-of-session silence means nothing.
      *Condition: confirm it fires on an abrupt exit, not only a graceful quit.*
- [ ] **`SubagentStop` / `TaskCompleted` → ledger prompt for delegated work.** A subagent that
      edits source never sets `source_changed`, so the change can land unlogged. *Condition:
      determine whether a subagent shares the parent `session_id` or carries its own — that
      decides whether this is a flag update or state merging.*
- [ ] **`PermissionDenied` → guard-hit metrics.** Tier-0 denials are invisible after the fact.
      Reuse the `loop_detection.jsonl` channel.

Explicitly rejected, with reasons in the assessment: `UserPromptSubmit` (a blocking path in a
fail-open dispatcher), `FileChanged` (literal matcher vs a weekly-rolling ledger filename), and
the remaining 19 (no Phase 0–3 obligation attaches).

- [x] **Determine why a guard `ask` did not surface.** **Resolved 2026-08-06.** An `ask`
      requires a human present; a `deny` does not. Re-run interactively, `git rebase` produced
      the prompt and it was declined — from the same dispatcher and the same registration that
      had allowed it silently minutes earlier in an unattended session. That refutes the
      standing claim that `ask` fails as a class: one `ask` surfacing is sufficient, and the
      cause is the session, not this repository and not Claude Code's handling of
      `permissionDecision: "ask"`. Consequence recorded rather than filed away: the two
      artifacts carrying `enforcement_mode: ask` (`rule-no-heredoc-stdin`,
      `prohibition-rewrite-published-history`) are `live` over an **attended** session only,
      and their `enforcement_note`s plus GUIDE §7.5 now say so. The two prohibitions that must
      hold unattended — delete-ledger and force-push-shared — are both `deny`, and the `deny`
      path was observed blocking in the unattended session. Original record below.

      On 2026-08-06 a heredoc ran with no
      prompt while the dispatcher, replayed with the identical command, returned
      `permissionDecision: "ask"`. GUIDE §7.5 documents `dontAsk` turning an `ask` into a silent
      *block*; what was observed was a silent *allow*, which is undocumented. Until this is
      understood, an `ask` cannot be treated as a control.
      **Narrowed 2026-08-06 (post-move session), not closed.** A controlled run in a fresh
      session eliminated every cause internal to this repository. Same session, same
      `PreToolUse` registration, same `Bash|PowerShell` matcher, same script: `rm -rf history/`
      was **denied and blocked**, while a heredoc and `git rebase --help` — both of which the
      dispatcher returns `ask` for on replay — **ran with no prompt**. So the registration is
      live, the matcher covers `Bash`, and `guard_heredoc`/`guard_history_rewrite` are correct.
      No settings file carries `dontAsk`, a `permissions.deny`, or any mode override
      (`.claude/settings.json`, `.claude/settings.local.json`, `~/.claude/settings.json`; no
      managed-settings file exists). Independent corroboration that a session-level override is
      in play: `.claude/settings.json` sets `defaultMode: "plan"` and plan mode was **not** in
      effect either — a non-allowlisted write ran unprompted.
      **Remaining hypothesis:** the runtime resolves `ask` → allow when the session has no one
      to prompt (this session is flagged non-interactive) or was launched with permissions
      bypassed. Not observable from inside a session, so it is recorded as a hypothesis.
      **What would settle it:** run the identical heredoc in an *interactive* `claude` session
      started with no bypass flag. If the prompt appears, the cause is the session launch mode
      and `ask` is a real control under normal use; if it still runs silently, the cause is in
      Claude Code's handling of `permissionDecision: "ask"` and belongs upstream.

---

## Active Epic: Harden the hook dispatcher

- [x] Add CI (GitHub Actions) running the test suite on Linux + Windows.
- [x] Stop-hook Phase-3 auto-breadcrumb: on a dirty tree, record
      `plans/UNFINISHED.md` (marker-guarded, never clobbers a human plan) so an
      interrupted closure survives a force-close.
- [x] Opt-in F5 daily update check in `SessionStart` (`workflow_update_check`
      config; detection-only, once/day, off by default).
- [x] `main_branch` auto-detection: resolve the default branch from the local
      `refs/remotes/<remote>/HEAD` ref (no network), with an opt-in
      `git remote show` fallback and an explicit `stop_hook.main_branch` pin
      still taking precedence.
- [x] `--self-test` subcommand that validates config against
      `schemas/config_schema.json` and prints a health report. Ships with a
      stdlib schema-subset validator (no `jsonschema` dependency) and a
      governance maturity level (1–5), reported but never enforced.
- [x] Agent loop detection: `PostToolUse` tracks a signature of
      `(tool_name, tool_input)` and flags consecutive identical calls at a
      configurable threshold. Advisory only; logs to
      `.ai/08-behavioral-metrics/loop_detection.jsonl`.
- [ ] Structured logging to a rotating debug file when `WORKFLOW_HOOK_DEBUG=1`.
- [ ] Revisit `FileChanged` for the Stop flags if its matcher ever accepts globs.
      It is the right mechanism — it watches the disk, so it sees writes from any
      process — but the watch list is literal filenames and our ledger name rolls
      over weekly, so a static matcher would go stale in seven days. The mtime
      fallback covers it meanwhile (GUIDE §7.3, decision doc §9). The matcher-less
      probe remains inconclusive on **two** confounders, not three: this
      environment is Claude Code 2.1.221, so the event exists here (decision
      doc §10). Settling the rest needs a session restart with the probe
      registered, which one session cannot do to itself.

## Active Epic: Governance library growth

- [x] Library integrity tests (`tests/test_governance_library.py`): manifests vs
      disk, the required key set, the CISA risk taxonomy, the GUIDE §12 step
      mapping, `.ai/` vs `templates/ai-library/`, and — the load-bearing one —
      every `live` tier naming an `enforced_by` that resolves to real code.
      Found and fixed seven drifts in the v14 integration. `--self-test` now runs
      in CI, gated on exit code.
- [x] Harvest the `05-domains/` rules. **Ten** review categories, 80 items, every one
      citing a source with an authority tier and a `confidence_level` derived by
      `derive_confidence` rather than asserted. Written as questions, not
      prescriptions. Conditional loading is manifest data read by both skills.
      Full framework in `docs/checklist-system.md`.
- [x] Harvest the `03-planning/` rules. **Five** plan-review categories, 31 items,
      answered at Phase 1 before code exists — the phase `05-domains/` structurally
      cannot reach, since it reviews code *against* the plan. Selection moved to
      `.ai/00-system/checklist-selection.json` with a `workflow_phase` axis so one
      table serves both folders. Trialled against its own plan: 10 of 31 items
      found something.
- [ ] Verify a plan actually gets reviewed. `VER-PLN-04` asked this of the plan that
      built `03-planning/` and the answer was no: the tests check the checklists'
      *structure*, nothing checks that the questions were ever put to a plan. Probably
      a `Stop`-hook flag akin to `ledger_touched`, but a plan is not a file the hook
      can see, so this may be honestly unenforceable — in which case say so in the
      `enforcement_note` rather than leaving the gap unnamed.
- [ ] Act on the SOLID/clean-code trial findings in `.claude/hooks/workflow_hook.py`:
      `run_self_test` (~166 lines) and `handle_stop` (~89) each fail the "describe it
      without saying *and*" question, and 16 `except Exception: pass/return/continue`
      sites make the fail-soft design hard to debug. The checklist found these; acting
      on them is a refactor, not an audit.
- [ ] `06-components/`: write the first blueprint when a pattern has shipped and
      survived review twice. `BLUEPRINT_SCHEMA.md` defines the shape and the bar.
- [ ] `--self-test --json` for CI consumption, so a pipeline can assert a
      minimum maturity level without scraping the text report.
- [x] Fold `GUIDE.md`'s revision history into a sibling changelog — the table hit 8
      rows at v5.0 and tripped the §6.3 threshold at the v5.1 edit. Relocated to
      `GUIDE_CHANGELOG.md` (`exclude_from_ai: true`), latest 3 rows kept in place.
      Named for its document rather than `CHANGELOG.md`, which at the repository
      root would read as the project's changelog.
- [x] Decide whether Tier-0 prohibitions should become a `PreToolUse` hard block
      rather than a convention. **Done, and the answer was neither.** A
      `permissions.deny` rule cannot express "shared branch" and is bypassed by
      the PowerShell tool, so it took a parser after all — but emitting `ask`
      alongside `deny` dissolved the false-positive risk this item was deferred
      over. Force-push and audit-trail deletion `deny`; history rewrite and
      heredoc `ask`; `prohibition-commit-secrets` stays `convention` (see below).
      GUIDE §7.5, decision doc §8.
- [ ] Secret scanner for `prohibition-commit-secrets` — the one Tier-0 prohibition
      still unenforced. The `PreToolUse` guard sees the command, not the file
      contents, so it would only ever catch a secret typed inline. Real coverage
      means scanning `git diff --cached` on a `git commit`: entropy plus a small
      known-prefix set (`sk-`, `ghp_`, `AKIA`, PEM headers), stdlib-only, with a
      documented false-positive escape. Until it exists the tier stays honest.

## Active Epic: Adoption ergonomics

- [ ] `install.py` / `install.sh` to automate the §8.1 adoption steps.
- [ ] `settings.json` merge helper (idempotent insertion of the hooks block).
- [ ] Example projects (Python, Flutter) demonstrating end-to-end adoption.

## Backlog

- [ ] Documentation-Standard linter: scan `documentation_directories` and batch-report
      docs missing frontmatter or the required `version` / `last_validated` fields.
      Add a token-budget check that reads each doc's `estimated_tokens` and asserts it
      against its Progressive Disclosure layer limit (GUIDE §6.4 / Progressive Disclosure
      Guide §2, §8 — e.g. Procedural ≤ 2,000, Semantic knowledge file ≤ 5,000). Stdlib-only
      (no PyYAML dependency); reuse the frontmatter-fence parser rather than importing yaml.
      Also: (a) flag docs whose in-file Revision History exceeds ~8 rows as fold
      candidates (GUIDE §6.4); (b) **skip any file carrying `exclude_from_ai: true`**
      (a doc's sibling `CHANGELOG.md`) from both the token-budget assertion and any
      context-assembly path — mirror the guard already in the Progressive Disclosure
      retrieval script's `load_md_files()`.
- [ ] Ledger summarizer: roll a week's entries into a release note.
- [ ] PreToolUse guard to warn before editing files flagged `official: unknown`.

## Completed Epics

_(none yet)_
