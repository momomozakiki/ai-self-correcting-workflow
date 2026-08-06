# Contributing improvements upstream

When you find a flaw or a missing trigger in the workflow itself — not in the project using
it — classify it and log the discovery in the project ledger with a `[workflow]` tag.

| Criticality | What it covers | What to do |
|---|---|---|
| **High** (a.k.a. **Critical**) | Breaks invariants, loses data, or has security impact | Fix locally on `fix/<desc>` now, push, open a PR. You may use the fix immediately. |
| **Medium** | Missing trigger, ambiguity, non-critical bug | Open a `proposal/<desc>` PR with a plan. **Do not** apply it locally until merged. |
| **Low / non-critical** | Polish, wording, nice-to-have | Open an issue. Optionally a draft branch, no PR. |

"High" is the top tier. "Critical" is another name for it, not a level above it.

If you vendored the files and have no submodule to push to, file a GitHub issue using the
**Workflow bug / flaw report** template instead of pushing a branch.

The full process is in `.claude/workflow-core/CONTRIBUTING.md`.
