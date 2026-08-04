# Roadmap — Adaptive Self-Correcting Workflow

Planned improvements to the workflow itself. The `SessionStart` hook parses the
first `**Next action:**` line below and surfaces it at session start.

**Next action:** Structured logging to a rotating debug file when `WORKFLOW_HOOK_DEBUG=1`.

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
      fallback covers it meanwhile (GUIDE §7.3, decision doc §9).

## Active Epic: Governance library growth

- [x] Library integrity tests (`tests/test_governance_library.py`): manifests vs
      disk, the required key set, the CISA risk taxonomy, the GUIDE §12 step
      mapping, `.ai/` vs `templates/ai-library/`, and — the load-bearing one —
      every `live` tier naming an `enforced_by` that resolves to real code.
      Found and fixed seven drifts in the v14 integration. `--self-test` now runs
      in CI, gated on exit code.
- [ ] Harvest the first `05-domains/` rules from real tasks (the folder ships
      empty on purpose — see `.ai/GROWTH.md`).
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
