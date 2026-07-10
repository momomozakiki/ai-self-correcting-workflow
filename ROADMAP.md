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

- [ ] Provenance linter: scan `documentation_directories` for missing
      `SOURCE-PROVENANCE` and report as a batch.
- [ ] Ledger summarizer: roll a week's entries into a release note.
- [ ] PreToolUse guard to warn before editing files flagged `Official: Unknown`.

## Completed Epics

_(none yet)_
