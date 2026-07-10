# Contributing to the Adaptive Self-Correcting Workflow

The workflow is a living system. Any project that uses it is encouraged to
propose improvements — after merge, every other project inherits them on its
next update. This document is the §10 contribution process from `GUIDE.md`.

## 1. Detect & classify

When you (agent or human) find a flaw, missing trigger, or improvement:

1. **Identify** the issue (hook bug, missing conditional trigger, unclear docs…).
2. **Classify its criticality** and act accordingly:

| Criticality | Definition | Immediate action? |
|-------------|------------|-------------------|
| **High** | Fails to enforce invariants, risks data loss, session-breaking bug, security hole. | **Yes** — fix locally now, submit PR. |
| **Medium** | Missing trigger, inefficient process, ambiguity, non-critical logic error. | No — propose a plan; don't apply until approved. |
| **Low** | Cosmetic, wording, minor edge case. | No — open an issue or low-priority branch. |
| **Non-critical** | Observation, suggestion, future enhancement. | No — open an issue only. |

3. **Log the discovery** in the project's own `history/YYYY-Www.md` with a
   `[workflow]` tag.

## 2. High-criticality — immediate fix

```bash
cd .claude/workflow-core
git checkout -b fix/<short-description>
# make the fix
git commit -m "fix(high): <description>"
git push origin fix/<short-description>
```
Open a PR explaining the flaw, why it's high, and the fix. You may use the fix
immediately by staying on that branch; the submodule updates officially after
merge. Notify the user.

## 3. Medium-criticality — proposal & plan

- Create `proposal/<description>`; include a detailed plan (markdown or commits).
- Push and open a PR with a clear title and explanation.
- **Do not apply locally** until merged (unless the user explicitly requests it).
- If the change touches docs, update the relevant `SKILL.md` / spec in the same branch.

## 4. Low / non-critical — report only

```bash
gh issue create --title "..." --body "..." --label low   # or non-critical
```
Optionally push a draft branch, but leave PR creation to the maintainer.

## 5. Proposing a new checklist item (trigger / step)

Treat as **Medium**. In the proposal branch, add the item to the relevant
section of `GUIDE.md` (and `SKILL.md`) with rationale, examples, and its
interaction with existing steps. Submit a PR; don't enforce locally until merged.

## 6. After contribution — sync & cleanup

- Track significant PRs/issues in the project roadmap.
- After merge, the daily update check (F5) detects new commits: update the
  submodule, verify the fix, and log the update in the ledger.
- If a high-criticality fix was applied locally before merge, ensure the
  submodule fast-forwards cleanly.

## Branch naming

- `fix/<description>` — high-criticality fixes
- `proposal/<description>` — medium changes
- `low/<description>` — low / non-critical (optional)

## Before you push

Run the test suite — it must stay green and dependency-free:

```bash
python -m unittest discover -s tests
```
