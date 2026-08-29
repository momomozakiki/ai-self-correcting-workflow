# The governance library (`.ai/`)

Loaded every session — no `paths:` gate. The mirror requirement below is violated by editing a
single file, so it cannot wait until something under `.ai/` is opened.

Full rationale: `GUIDE.md` §13.

## Enforcement status is a claim about reality, not a label

Every artifact declares one:

| Status | Means | Must carry |
|---|---|---|
| `live` | A hook or test actually enforces it | `enforced_by`, a list of `path::symbol` references that resolve to real code |
| `convention` | Followed by discipline; nothing blocks | `enforcement_note` saying **what is missing**, not just asserting the rule |
| `declarative` | Recorded only | A `reason`, with the unavailable fields written as `null` |

**Never imply enforcement that does not exist.** Write declarative fields as `null` with a
reason — never faked, never aspirational. `tests/test_governance_library.py` holds each of these
sentences to an assertion, including the inverse: a `convention` artifact that names an
`enforced_by` fails, because it is either under-tiered or bluffing.

Naming a function is not evidence it runs. `resolve_enforcer` proves `guard_force_push` exists;
only a settings entry proves Claude Code ever calls it. That gap is why `SettingsWiring` checks
both settings files.

## The mirror requirement is gone — `.ai/` is being retired

**Changed 2026-08-29.** `templates/ai-library/` was deleted and `TemplateParity` with it
(stage 1 of `plans/golden-rules-migration.md`). **Do not mirror `.ai/` anywhere.** There is no
longer a second copy to keep in step, and the instruction that used to sit here would now send
you to a directory that does not exist.

`.ai/` itself is still live and still the authority until stage 3 ports it to `golden-rules/`.
Its rules are unchanged; what went away is the obligation to maintain a duplicate of them for
adopters.

The mirror *principle* still applies where it has a subject: `.claude/rules/`,
`.claude/agents/` and `.claude/skills/` each mirror into `templates/`, in the same commit,
enforced by `test_claude_layout.TemplateMirrors` and `test_skills.SkillTemplateParity`. Both
gained non-empty-corpus guards, because two empty trees compare equal and pass.

Adding a rule means: the rule file and its folder's `manifest.json` (including `total_items`).
A rule with `maps_to_v14_step: null` needs no `GUIDE.md` §12 row — `StepMapping`
skips null steps — but any non-null step must exist in that table with a matching tier.

## Where things live

- `.ai/01-phases/` — one rule per workflow step, keyed to Phase 0–3.
- `.ai/02-market-rules/prohibitions/` — Tier 0. Three are `live`;
  `prohibition-commit-secrets` is deliberately `convention`, because the guard sees tool calls
  and has no way to detect a secret.
- `.ai/03-planning/` — plan review at Phase 1, before code exists.
- `.ai/05-domains/` — review checklists, phrased as **questions** rather than prescriptions so
  they carry to any project and leave judgement intact. All `convention`.
- `.ai/06-components/` — stays empty until a pattern has shipped and survived review.
  `BLUEPRINT_SCHEMA.md` sets the bar.

Health: `python .claude/hooks/workflow_hook.py --self-test`. The exit code reflects
**validation only**; the individual checks are reported, never enforced.

The **maturity level 1–5 no longer exists** (removed 2026-08-29). It rewrote a tracked file on
every run, so merely running the suite dirtied the working tree — an instrument that mutates
what it measures. It was also "reported, never enforced": a number nothing consumed, which
reads as a score, and a score invites optimising the score.
