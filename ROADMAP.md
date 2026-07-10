# Roadmap — Adaptive Self-Correcting Workflow

Planned improvements to the workflow itself. The `SessionStart` hook parses the
first `**Next action:**` line below and surfaces it at session start.

**Next action:** Wire up CI to run `python -m unittest discover -s tests` on every push.

---

## Active Epic: Harden the hook dispatcher

- [ ] Add CI (GitHub Actions) running the test suite on Linux + Windows.
- [ ] Optional `main_branch` auto-detection via `git remote show origin`
      (currently defaults to `main`, overridable in config).
- [ ] `--self-test` subcommand that validates config against
      `schemas/config_schema.json` and prints a health report.
- [ ] Structured logging to a rotating debug file when `WORKFLOW_HOOK_DEBUG=1`.

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
