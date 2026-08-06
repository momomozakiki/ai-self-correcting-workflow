# Handover — plan review

**Run date:** 2026-08-05 · **Branch:** `feat/governance-v14-integration`
**State:** 189 tests pass · `--self-test` **5/5 on its own merits** · `.ai/03-planning/` is new

Read this before the diff. It is the whole record of decisions taken without asking you.

---

## 1. What you asked for, and what it turned out to be

> *"the checklist is not for code only it should also for planning"*

Correct, and worse than it looked. Every rule in `.ai/05-domains/` carries the same
`ai_action`: *"work through the checklist against the code in question."* Ten categories,
eighty items, all of which need code to exist first. Meanwhile
`.ai/01-phases/rule-task-checklist.json` instructed the agent to *produce* a plan checklist
and supplied nothing to interrogate it with.

**So a plan was reviewed by nothing** — and not by oversight. Code review measures code
*against* the plan, so it will happily confirm that a well-built thing was built well when
the thing should not have been built at all. No amount of Phase-2 review reaches a defect
one level up.

`.ai/03-planning/` closes it: 5 categories, 31 items, answered at Phase 1.

## 2. Two things you were owed, now closed without you

- **Your Claude Code version is 2.1.221.** Read from the extension directory
  (`~/.vscode/extensions/anthropic.claude-code-2.1.221-win32-x64`). `/status` is a
  CLI-terminal command and the extension does not have it — I should not have sent you
  looking. Two version gates resolve: `FileChanged` **does** exist in this build (that
  confounder is eliminated, two remain), and `/model opus` **does** resolve to Opus 5.
- **`task_size` is closed as my judgement, unconfirmed by you.** Confirming it after the
  fact changes nothing — the run is committed and the checklists already loaded. Going
  forward the skill states the size *and the reason in the plan*, where objecting is free
  and actually changes what loads.

## 3. Items dropped for want of a source

The protocol's rule is that an unsourced item does not ship.

| Dropped | Why it did not resolve |
|---|---|
| *"Is the estimate realistic?"* | No standard fixes what makes an estimate realistic; every authority I checked treats estimation as a practice, not a criterion. |
| *"Does the plan fit in one sprint / two weeks?"* | The interval is folklore — the same defect as the "new developer in one week" item dropped last run. |
| *"Is the right person assigned?"* | PMBOK 7 covers it, but a single-operator project has no assignment decision to review. |
| Numeric plan-quality scores | Nothing fixes a threshold, and a score would be the confidence-percentage failure again. |
| ~15 further items | Restated an item already present, or I could not resolve a citation at authority ≥ 5. |

## 4. Decisions taken on your behalf

| Decision | Rejected alternative | Why |
|---|---|---|
| New folder `03-planning/` | More categories inside `05-domains/` | That folder's identity is code review; its every `ai_action` says "against the code". Planning also selects on a different axis. |
| Selection table → `.ai/00-system/checklist-selection.json` | Leaving it in `05-domains/manifest.json`, second copy for planning | A domain manifest cannot be the authority on a folder it does not contain. Two tables are two answers. |
| `workflow_phase` on every checklist rule | Phase implied by folder | Implied means re-derived at every read site. A test now holds the manifest and the rule to the same value. |
| Planning rules never tech-gated | Same `tech_stack_required` treatment as domains | A stack filter at Phase 1 could only ever exclude a question that still applied, silently. |
| Cite **IEEE 1012-2024** | IEEE 1012-2016, which I would have written from memory | 1012-2016 is superseded; 1012-2024 was published 2025-08-22. |
| ISO 31000 worded as *"does the plan identify…"* | *"ISO 31000 requires…"* | It is guidance and explicitly not certifiable — the same overstatement class as the NIST 800-190 defect corrected last run. |

## 5. Assumptions

- **Authority tiers**: ISO/IEC/IEEE and IEEE standards at 10, INCOSE/NASA/Google SRE at 8,
  Threat Modeling Manifesto at 7, Nygard at 5. My reading of the protocol's table.
- **`source_established` is deliberately conservative** — for ISO 31000 I stored 2018
  rather than the 2009 first edition, which understates age and therefore understates
  confidence. Wrong in the safe direction.
- **Task size for this run: `major_refactor`.** It moved the selection mechanism and
  touched all ten domain rules, both skills and a phase rule.

## 6. Not verified — and one of these is load-bearing

- **`ALT-RAT-05`, unanswered: a plan reviewed by the same agent that wrote it has no
  independent signal.** This is the honest limit of the whole folder. The only real
  mitigation is you reading the answers. Recorded in `docs/checklist-system.md` §5a rather
  than papered over, but not solved — and I do not know how to solve it from inside one
  agent.
- **Nothing checks that a plan actually gets reviewed.** `VER-PLN-04` asked this of its own
  plan and the answer was no: the tests check the checklists' *structure*, and a plan is not
  a file a hook can see. New ROADMAP item, and it may turn out to be honestly unenforceable.
- **Item content quality is untested.** Structure is held by 189 tests; whether
  `REQ-CHR-03` is a *good question* is not the sort of thing a test decides.
- **`source_consensus` counts are still my estimates**, as last run. Most worth challenging
  here: `REQ-CHR-01` and `REQ-CHR-03`, where I claimed 4.

## 7. Awaiting your ratification

Six new `convention` artifacts: five rules in `.ai/03-planning/` plus
`.ai/00-system/checklist-selection.json`. I authored them; you have not agreed to them.
Ratified items move to `.ai/10-ratification-archive/`.

**Plus one breaking change to accept or revert:** the selection table's new path. Any
adopter who vendored the library before today and reads `selection` from
`05-domains/manifest.json` will find it gone. The migration note is in
`docs/checklist-system.md` §5.

## 8. What broke during this run

- **The negative control proved nothing, twice.** First run: the baseline was already red
  from an in-flight mirror, so all eight breakages reported `FAILED` regardless — "8/8
  caught" was meaningless. Second: the control's own `.bak` sat inside `.ai/` and each
  broken file diverged the mirror, so `TemplateParity` fired every time whether or not the
  intended check did. Only the third version — asserting the *name* of the test that must
  catch each breakage — was evidence. Two breakages got reattributed in the process.
- **The version was one directory listing away** and I asked you for it twice instead.
  Logged as **recurring** in `RETROSPECTIVE.md` against the 2026-08-04 entry; it now owes a
  rule: a claim that something cannot be determined is itself a claim.
- **PowerShell mangled the ledger append** — `Get-Content`/`Add-Content` re-decoded UTF-8 as
  ANSI and every `§` became `Ã‚Â§`. Reverted and re-appended as bytes.

## 9. Evidence

| Check | Result |
|---|---|
| Negative control | **14 of 14** caught by the check that should catch each — green baseline, attributed by test name |
| Trial against a real plan | **10 of 31 items** found something in the plan that built them |
| Suite | 189 pass (5 new) |
| `--self-test` | 5/5, level 5 (Optimized) |
| Mirror | `.ai/` ↔ `templates/ai-library/` byte-identical outside the 5 exemptions |
