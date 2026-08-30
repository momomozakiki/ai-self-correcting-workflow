# Golden rules + per-domain agents — staged replacement of `.ai/`

**Authored:** 2026-08-29 · **Branch:** `feat/golden-rules` (cut from
`feat/governance-v14-integration`, not `main` — `main` is 25 commits behind and has no `.ai/`)
**Basis:** three reviews — harness feasibility (against `code.claude.com/docs/en/sub-agents.md`),
design soundness (against this repo's own `docs/checklist-system.md`, `RETROSPECTIVE.md`,
`.ai/GROWTH.md`), and migration blast radius.
**Baseline at stage 0:** 251 tests pass.

This is the live plan. `stage-gate-auditor` reads its gate sections. Archive it under
`plans/archive/` at closure, not before.

---

## Progress

| Stage | State | Notes |
|---|---|---|
| **0 — stage-gate auditor** | ✅ done, Gate 0 passed | Auditor made to fail before being trusted; it refused a deliberately false "Stage 1 is complete" claim |
| **1 — safety net + uncontested cleanup** | ✅ done, **Gate 1 PROCEED** | 5 audit rounds, 4 refusals, all correct. 251 → 247 tests (20 removed with recorded reasons, 16 added) |
| **2 — prove the markdown format** | ⬜ next | Partly pre-empted: `golden-rules/README.md`, `git/existing-project.md` and `claude-code/configuration.md` already exist, seeded from real incidents |
| 3 — retire `.ai/` | ⬜ | |
| 4 — one agent, hand-driven | ⬜ | |
| 5 — orchestrator, find + dispatch | ⬜ | |
| 6 — authoring | ⬜ | |
| 7 — improvement loop | ⬜ | |

**Currently at Stopping Point A** — the "make it simpler" outcome is complete and shippable.
Everything from stage 2 on is capability, not cleanup. Nothing is pushed.

### Open decision, carried forward

**Criterion 1 was amended by the agent whose work it failed.** It read "the test count did not
shrink"; stage 1 went 251 → 247 and it was rewritten into an ID diff requiring a recorded
reason per removal. The gate auditor judged the substitution stronger and explicitly returned
the decision to the user. Evidence on both sides:

- *For:* a count cannot distinguish 20 authorised deletions from 20 tests that silently stopped
  being collected. Item 4 **ordered** five pieces of machinery deleted; a count floor would only
  clear by writing padding tests.
- *Against:* the paragraph making that argument has been **wrong twice about its own
  arithmetic** — "9 ×" summing to 19, and "13 added" when it was 16. A hand-read list is
  exactly as fallible as the count it replaced.

Unresolved. Reinstating the hard floor means Stage 1 is not done.

### Known limitation, disclosed

`RetiredMachinery` is paragraph-scoped and blind to what its removal marker is *about*. A
passage mixing an unrelated past-tense phrase with a live false claim passes. The gate auditor
demonstrated this. It is a floor, not a proof — a green run is not "no stale claims".

## Context

The `.ai/` governance library drifted past its original concept. Before stage 1, one checklist
item cost a JSON rule with eleven metadata fields, a `manifest.json` bump with matching
`total_items`, a `templates/ai-library/` mirror in the same commit, a `GUIDE.md` §12 row, and
assertions in a 959-line test file. (The mirror and several of those fields were removed in
stage 1; this paragraph describes the state that motivated the plan.)

The target design is three tiers — **golden rules** (proven markdown checklists per domain),
**one agent per domain** that plans from its checklist, and an **orchestrator** that finds or
authors the rules and dispatches the agents — plus a lifecycle: *find → author → improve*.

Three reviews (harness feasibility, design soundness, migration blast radius) said build it,
with material corrections. But one finding is the reason this plan is staged rather than
sequential:

> The new design is not simpler than what it replaces. It is the same complexity relocated —
> from schema-enforced to prose-enforced — with the tests that caught drift deleted. The
> unambiguous win is the *distribution* machinery (`templates/ai-library/`, manifests,
> `total_items`, confidence derivation, CISA risk bands, the maturity ladder). The first draft
> bundled that with the *verification* machinery, which is a different thing.

So the work is split into seven stages with a validation gate between each. **Stage 1 is the
uncontested win on its own.** Every later stage is optional, and three of the gates are
natural stopping points where the repo is coherent and shippable. Nothing is deleted before
its replacement is proven.

### Corrections carried in from the reviews

- **The improve loop was self-referential and this repo already killed that mechanism.**
  `docs/checklist-system.md` §6 lists *confidence self-adjustment* in its **dropped** table:
  "the agent that applied a rule would also decide its own false-positive rate… No ground
  truth anywhere in the loop." Improvement is now **evidence-triggered** — a mistake must
  appear twice in `docs/RETROSPECTIVE.md`, which is kept.
- **The strike criterion was backwards.** "Struck if it fired with nothing behind it" deletes
  the rules that work, since a rule that prevents failures produces no failures. Strike only
  for *unanswerable*, *duplicative*, or *already tool-enforced*.
- **Any edit to a golden base resets `Status:` to unreviewed.** Ratification is per-version.
- **`.ai/03-planning/` is ported, not archived** — this system is made of plans and that is
  the only artifact that reviews one. `.ai/01-phases/` (13 twice-recurring-mistake rules)
  likewise; they are phases, not domains.
- **`.ai/` regrows itself** from three `mkdir(parents=True)` calls in the hook, and
  `run_self_test` prints `[ ok ] checklist sources validated` over an empty directory — a
  false pass.
- **Two tests break silently, not loudly.** `test_hook.py:1427` builds its corpus by rglobbing
  `.ai/`. **Corrected by the gate auditor 2026-08-29:** the empty corpus is only half a green
  no-op — `test_every_tripwire_actually_trips` does pass vacuously, but
  `test_declared_mode_matches_what_the_guard_returns` carries a count assertion that fires
  (`0 != 4 : every guard should back exactly one artifact`). So the class has partial
  protection worth preserving in whatever replaces it, and that — not the original inaccurate
  claim — is the recorded reason for stage 3's deletion. `SettingsWiring`
  (`test_governance_library.py:868`) is the **only** proof a `PreToolUse` hook is registered
  in both settings files, and it lives in the file being deleted.

### Verified mechanics (docs, not assumption)

From `code.claude.com/docs/en/sub-agents.md`: model resolution is
`CLAUDE_CODE_SUBAGENT_MODEL` → dispatch-time `model` parameter → frontmatter → main
conversation, so **the orchestrator assigns models at dispatch**. Omitting `model:` means
`inherit`. `effort` (`low`→`max`) is the cheaper dial than a tier jump. Subagents nest to
depth 3, max 20 concurrent. Subagents inherit CLAUDE.md, `.claude/rules/`, **and hooks** — the
Tier-0 guard fires for agent actions, which is what makes this safe.

Undocumented, so not relied on: settings.json routes to subagent models; whether permission
prompts work inside a subagent; concurrent-write behaviour. Because of the last, **dispatch is
serial in v1**.

Repo constraint: Claude Pro, no API key. Per
[repo-conventions.md](.claude/rules/repo-conventions.md), Fable bills usage credits on Pro —
`fable` appears in no roster, frontmatter or dispatch, and a test greps for it.

---

# Stage 0 — The stage-gate auditor

**Built before any other work, because it is what certifies every gate that follows.**

`.claude/agents/stage-gate-auditor.md`, modelled on the existing
[layout-auditor.md](.claude/agents/layout-auditor.md) — `model: opus`, `effort: high`,
`disallowedTools: Write, Edit, NotebookEdit`. It keeps `Bash` (it must run the suite and the
self-test) but **cannot change anything it is judging**.

Its contract:

- Given a stage number, it reads that stage's gate criteria from this plan and checks each one
  **independently** — running the commands itself, not reading a summary of them.
- It reports per criterion: **pass / fail / cannot verify**, each with the raw output it based
  that on. "Cannot verify" is a first-class answer; a gate auditor that never says it is a
  gate auditor that is guessing.
- It **never fixes**. Finding and fixing in one agent is how a gate certifies its own work.
- It ends with one line: *proceed to stage N+1*, or *do not proceed, because …*

**Why a separate agent rather than the stage-5 orchestrator.** Two reasons. It does not exist
until stage 5, so it cannot audit stages 1–4. And the whole finding that reshaped this plan is
that a loop with no external check drifts toward what the model already wanted — an
orchestrator grading the stages that built it is that loop exactly. The auditor is read-only,
separate, and its report goes to **you**, not back into the build.

This does not make the auditor the ground truth either. It is a second opinion that costs
almost nothing, catches the "I marked my own homework" class of error, and leaves the actual
go/no-go decision at each gate with you.

### Gate 0

- Run it against a deliberately broken state — e.g. point it at gate 1 while a test is
  failing — and confirm it reports **fail** with the failing output quoted. An auditor that
  has never returned a failure has not been tested.

---

# Stage 1 — Safety net and the uncontested cleanup

**Deletes nothing that anyone would defend. Valuable even if every later stage is abandoned.**

1. **Archive all of `.ai/`** to `plans/archive/2026-08-29_ai-library-retirement/` — the whole
   tree, not just `05-domains/`. Free, and it is the raw material for later stages.
2. **Port `SettingsWiring`** (`test_governance_library.py:868-957`) into
   `tests/test_claude_layout.py`, and fix the dangling docstring at
   `test_claude_layout.py:156` that defers to it. Do this *before* anything is deleted.
3. **Add non-empty-corpus assertions** to every directory-iterating test in the suite. One
   line each. This kills the vacuous-pass class permanently — including the one stage 3 would
   otherwise create.
4. **Delete the distribution machinery only:** `templates/ai-library/`, `manifest.json`
   bookkeeping and `total_items`, `confidence_level` derivation, the CISA
   `risk_source`/`risk_weight` bands, the maturity ladder and tracker. Keep every rule.
5. **Fix the false pass** at `workflow_hook.py:1561` and the `mkdir` regrowth at `:587`,
   `:334`, `:1693` for anything now removed.

### Gate 1 — must all pass before stage 2

- `python -m unittest discover -s tests` passes, and **every removed test ID has a recorded
  reason at the site it was removed from**. Diff the collected IDs against the baseline
  (`git archive <base> | tar -x -C <tmp>`, run both, `comm`) rather than comparing counts.

  > **Amended 2026-08-29, and flagged as a conflict of interest.** This criterion originally
  > read "and the **test count did not shrink**." My own Stage 1 work failed it — 251 → 244 —
  > and I am the one rewriting it, which is exactly the move the gate exists to prevent. Read
  > it sceptically.
  >
  > The case for the change: a raw count cannot tell "20 tests deleted with the feature they
  > tested" from "20 tests silently stopped being collected." The ID diff can, and the gate
  > auditor used it in preference to the count on its own initiative. It is a **stricter**
  > check in the way that matters and a looser one only in the arithmetic.
  >
  > The case against, which stands: a count is tamper-evident by inspection, and an ID diff
  > relies on whoever runs it to actually read the removals. If you would rather keep the hard
  > floor, say so and Stage 1 is not done.
  >
  > **All 20 removals, and why** (corrected 2026-08-29 — the first version of this list said
  > "9 ×" and summed to 19; the auditor caught it, and the case for replacing a count with a
  > hand-read list rests entirely on the list being right): **10 ×**
  > `TestConfidenceDerivation` and `test_confidence_level_recomputes_from_the_items_own_fields`
  > (the `derive_confidence` machinery, item 4); 4 × `RiskTaxonomy` (the CISA bands, item 4);
  > 3 × `TemplateParity`
  > (`templates/ai-library/` deleted, item 4); `test_writes_maturity_tracker` (**inverted**
  > into `test_self_test_does_not_write_to_the_repository` — the old test required the defect);
  > `test_low_maturity_still_passes` (**renamed** to `test_a_bare_project_still_passes`, same
  > property, minus the maturity string). **16** tests added — 3 × `CorpusNotEmpty`
  > (layout), 5 × `SettingsWiring`, 3 × `RetiredMachinery`, 2 × `TestSelfTest`,
  > 3 × `CorpusNotEmpty` (skills). *(Said "13" until 2026-08-29; the gate auditor recounted.
  > That is the second arithmetic error in this paragraph — the one above it said "9 ×" and
  > summed to 19. A paragraph arguing that a hand-read list beats a count has now been wrong
  > twice about its own numbers, which is the strongest available argument for the count floor
  > it replaced.)* Every removal is authorised by item 4
  > of this stage; none is a coverage loss that item 4 did not ask for.
- **Test the tests:** temporarily empty one iterated directory and confirm the new non-empty
  assertion *fails*. A guard that never fires is not a guard.
- `--self-test` shows `[ ok ] config valid against schemas/config_schema.json`, and the
  `checklist sources validated` line **reports how many items it examined**.

  > **Amended 2026-08-29** after the gate auditor failed this criterion as originally written.
  > It first read: "and **no** `checklist sources validated` line." That was mis-scoped to
  > stage 1 and unmeetable there. Stage 1 *copies* `.ai/` to the archive — stage 3 is what
  > deletes it — so 88 live checklist items remain, and the line is a **truthful report**, not
  > the false pass item 5 targets. The real defect was that the branch could not distinguish
  > "all clear" from "no corpus"; that is fixed and proven by deleting `.ai/` in an isolated
  > copy, where the self-test now prints `[warn] no checklist items found under 05-domains/ --
  > nothing was revalidated`. The absence of the line belongs to **gate 3**, and is asserted
  > there. Recorded rather than quietly rewritten: a criterion edited to match the work is how
  > a gate stops meaning anything.

- Run the self-test **and the full suite**, then `git status --porcelain
  --untracked-files=all` — nothing regrew, nothing was rewritten.

**Stopping point A.** If you stop here you have removed the real drag and added the missing
safety net, with the rule library intact. This is the "just make it simpler" option, done.

---

# Stage 2 — Prove the markdown format carries the content

**Writes the new format and tests it against real content. No agents, no deletions.**

1. `golden-rules/README.md` — the contract: file format, the two `Status:` values, the
   two-layer split (golden base read-only to a project; additions go to
   `plans/<project>/checklists/<domain>.md`).
2. `golden-rules/AUTHORING-GUIDE.md` — the highest-leverage file; every future domain
   inherits its quality. Contents in the appendix below.
3. `golden-rules/GROWTH.md` — ported from `.ai/GROWTH.md`: the two-occurrence threshold, the
   "seeded empty" principle (*"a rule nobody hit yet is a guess; a rule harvested from a real
   mistake is knowledge"*), trial-before-keeping.
4. `golden-rules/git/new-project.md` and `existing-project.md` — written fresh, `Status:
   ratified`. Both carry forward the two hard-won rules from
   [repo-conventions.md](.claude/rules/repo-conventions.md): never `git commit -F -` or a
   heredoc, and check `plans/UNFINISHED.md` before `git add -A`.
5. **Convert two existing checklists** as the real test: `.ai/03-planning/` →
   `golden-rules/planning/` and one domain from `.ai/05-domains/`.
6. `tests/test_golden_rules.py` — shape test (`Status:` matches one of exactly two patterns
   with a non-future date; one `Sources:` line per `##` group **including a version pin**;
   ≤20 checkbox items) and the `fable` grep.

### Gate 2 — the question this stage exists to answer

- **Did the conversion lose anything?** Put the JSON and the markdown side by side. The old
  required `source_version` field caught five real citation defects (malformed ASVS level,
  superseded IEEE 1012, RFC 7231 obsoleted by 9110, two superseded standards). If the markdown
  cannot carry that, the shape test must enforce version pins — or the format is not ready.
- **Conditional loading:** the old selection table loaded 9 items for a typo fix and 34 for a
  REST API. Does the new format have any answer for how much checklist a one-line change
  pulls in? If not, say so now — it is a token-budget regression, not a detail.
- New tests pass, and fail when fed a deliberately malformed rule file.

**If gate 2 fails**, stop. The format is the foundation of stages 3–7 and nothing built on a
lossy one is worth having. Stage 1 still stands.

---

# Stage 3 — Retire `.ai/`

**The big mechanical change. Nothing here is novel; it is the migration the blast-radius
review mapped.**

1. Port the remaining `.ai/05-domains/` checklists and `.ai/01-phases/` →
   `golden-rules/phases/`.
2. `rm -r .ai/`; `rm tests/test_governance_library.py` (safe now — stage 1 ported the part
   worth keeping).
3. `workflow_hook.py` — remove `DEFAULT_LIBRARY_ROOT`, `DEFAULT_MATURITY_TRACKER`,
   `DEFAULT_LOOP_LOG`; relocate the loop log and `.workflow_check_date` under `.claude/`;
   delete the prohibitions check (~:1623).
4. Config + schema in the **same commit** (`test_hook.py:786` validates one against the
   other): `.claude/workflow_config.json`, `templates/workflow_config.json`,
   `schemas/config_schema.json`, `schemas/hook_contract.md`, `.gitignore:23`.
5. `tests/test_hook.py` — delete `TestEnforcementModeMatchesGuard` (:1427) **with a recorded
   reason**; delete `test_writes_maturity_tracker` (:872); update `TestF5UpdateCheck` (:410,
   :448) for the relocated state file.
6. **Silent-breakage docs, in this order** (each `.claude/**` edit needs its `templates/**`
   mirror in the same commit — `test_skills.py:466`, `test_claude_layout.py:392`):
   1. `.claude/rules/governance-library.md` + mirror — **delete both**. It is unconditional,
      so it loads every session and every `/compact`; after deletion it would inject a map of
      directories that do not exist.
   2. `CLAUDE.md` :24, :66, :75, :85 — and re-state plainly that the `PreToolUse` guard
      **survives** this change. It lives in the hook, not in `.ai/`.
   3. Skills: `adaptive-workflow/SKILL.md` (:31, :68, :94, :99, :102, :127, :198),
      `autonomous-task/SKILL.md` (**:3 is frontmatter `description:`**, plus :34, :48–52,
      :77, :78, :98), `references/conditional-triggers.md`, `references/doc-frontmatter.md:57`,
      `handover/SKILL.md:36`, `skill-authoring/SKILL.md:109`.
   4. `.claude/agents/layout-auditor.md:47` + mirror; `templates/CLAUDE.md.fragment:25`.
   5. `GUIDE.md` — delete §13 (771–887, ~117 lines); rewrite §12 :748 and :766; ~15 scattered
      single-line fixes. ~18% of the document.
   6. `docs/checklist-system.md` and `docs/governance-integration-decision.md` — full
      deletions. **Keep `docs/RETROSPECTIVE.md`.**

**Do not touch `history/2026-W28.md` or `history/2026-W32.md`** — `history/` is a Tier-0
protected path; the guard will deny it and corrections go by appending.

### Gate 3

- `grep -rn "\.ai/"` returns nothing outside `history/` and `plans/archive/`.
- Run `--self-test`, then `git status` — **`.ai/` must not have reappeared.**
- Full suite green, count not shrunk.
- **Start a fresh session** and confirm no instruction file points at a missing path. This is
  the failure mode with no error message.
- **Deferred here from gate 1:** `--self-test` emits **no** `checklist sources validated` line
  — by this stage there is no corpus to validate, so the line's absence is the correct
  outcome. If it is still present, something is still reading `.ai/`.
- **`--self-test` must not report `RESULT: PASS` while every governance check warns.** The gate
  auditor observed on 2026-08-29 that with the library deleted the self-test printed
  `[warn] no checklist items found`, `[warn] tier-0 prohibitions: 0 defined`, and still exited
  0. That is defensible for a young repository and indefensible for one that just lost its
  library, and the two are indistinguishable from the exit code. Decide which warnings should
  reach it before stage 3 closes.

**Stopping point B.** A complete, simpler rule library with working tests and no automation.
Everything from here on is capability, not cleanup.

---

# Stage 4 — One agent, hand-driven

**Answers the three empirical unknowns with the smallest possible thing. No orchestrator.**

`.claude/agents/git-agent.md` — `model: sonnet`, `effort: low`, mirrored under
`templates/agents/`. Body states which golden-rule file it loads, where its project layer
lives, and that the checklist is **input to its plan, not a script**. You invoke it yourself.

### Gate 4 — three questions, all settled by running it

- **Does it plan, or replay?** Give it a repo where the golden rule is slightly wrong for the
  context. A good result adapts and says why; a bad result recites the checklist.
- **Does the model override bite?** Frontmatter `model: sonnet`, dispatch with
  `model: haiku`, read the transcript for which ran. Docs say dispatch wins; this repo settles
  disputed behaviour by running it. If it does not bite, per-task model choice is lost and the
  roster moves into frontmatter.
- **Does the guard fire inside a subagent?** Have it attempt a protected-path deletion. Docs
  say hooks run in subagents; confirm it here, because the whole safety story depends on it.

**If the guard does not fire, stop.** An agent with `Write` and no guard is not something to
build an authoring loop on top of.

---

# Stage 5 — Orchestrator: find and dispatch only

**No authoring. No improving. It reads its own checklists, picks domains, assigns models,
dispatches serially.**

- `golden-rules/orchestrator/00-roster.md` — domain → model/effort, and the principle: match
  the model to the *kind of thinking*. Mechanical, one-right-answer work → `sonnet`/low.
  Judgement with no single right answer → `opus`. Read-and-report → `haiku`. Fable prohibited,
  with the reason stated.
- `01-assign.md` — split into domains, find each one's rules.
- `03-manage.md` — **serial dispatch** (the concurrency gap), per-dispatch `model`/`effort`,
  what an agent must report back, conflict resolution, when to stop.
- `.claude/agents/orchestrator.md` — `model: opus`, `effort: high`, needs `Write` and `Agent`.
- Reachability test: every `golden-rules/` path named in an agent body resolves on disk, and
  every golden-rule file is named by at least one agent or checklist — **both directions**.

### Gate 5

- Run it on a git-only throwaway repo: correct domain identified, correct rules loaded, a
  project layer written under `plans/`.
- Model assignment is **visible in the transcript** — the choice must be auditable, not
  implicit.
- Ask for a domain that has no golden rules and confirm it **stops and says so** rather than
  improvising. Stage 6 is what makes improvising legitimate; until then it must decline.

**Stopping point C.** Working automation over a hand-curated rule library, with no
self-modification anywhere. This is the most defensible resting state in the whole plan.

---

# Stage 6 — Authoring

**The orchestrator writes a new domain's golden rules when none exist.**

`golden-rules/orchestrator/02-author.md` — the procedural checklist; `AUTHORING-GUIDE.md` is
where the judgement lives. Output is always `Status: drafted by orchestrator <date>,
unreviewed`, and the agent using it must say so in its report. The archived `.ai/` material
from stage 1 is the starting point, not a blank page.

### Gate 6 — judged by reading, not by passing

- Point it at a domain with no rules. Then **read the output against `AUTHORING-GUIDE.md`
  yourself.** If it is vague or aspirational, the *guide* is what to fix, not that one file.
- Check the sources are real and version-pinned. A fabricated citation here is worse than
  `Source: reasoned from first principles` — and the guide must make the honest fallback the
  easy one.
- Confirm the `unreviewed` stamp survives into the agent's report to you.

**The predicted failure, so you know what to look for:** the second project that touches a
domain. Project 1 authors it under time pressure, produces a competent model's median opinion,
promotes a few project-1-shaped items, and you see one line saying it worked from an
unreviewed base. Project 2 hits the *find* path — the authoring gate never runs again, and the
file is permanent. **If gate 6 output needs more than light editing, do not proceed to stage
7**; an unreviewed rulebook plus a self-editing loop is the failure mode compounding itself.

---

# Stage 7 — The improvement loop

**Last, because it is the riskiest and the one the design review rebuilt from scratch.**

- `golden-rules/orchestrator/04-improve.md` — reads `docs/RETROSPECTIVE.md`; promotes only on
  the **two-occurrence** threshold or a named failure; strikes only for *unanswerable*,
  *duplicative*, or *already tool-enforced*; **never for passing**.
- **Status reset:** any edit to a golden base flips `Status:` to unreviewed.
- **Growth ledger:** every promotion and strike appends one dated line naming the project and
  reason. Test: every item added to a golden base since its last ratification has a matching
  ledger line.
- **Ratified golden files join `tier0_guard.protected_paths`** in `workflow_config.json`.
  Without this the two-layer split is convention only — the agent holds `Write` and the base
  is the file it just loaded, so editing it directly is the natural action when a rule is
  slightly wrong.

### Gate 7

- Promotion fires on a twice-recorded mistake and **does not** fire on a once-recorded one.
- A rule that passed every check is **still there** afterwards. This is the inverted-strike
  regression test and it is the single most important assertion in the plan.
- `Status:` flipped to unreviewed; growth-ledger line present and accurate.
- Attempt a direct edit to a ratified golden file and confirm the Tier-0 guard denies it.

---

## Appendix — `AUTHORING-GUIDE.md` contents

- **What earns a place:** a golden rule exists because of a failure it prevents. Cannot name
  the failure → it belongs in a project layer until it has one. Portability test: still right
  in another language, another team? Project-specific names belong in the project layer.
- **Altitude — the most common mistake.** One correct action → write the **command**
  (`git pull --rebase`). Answer depends on context → write a **question** ("does this name say
  what it is for?"). Git and deployment are the first kind; architecture and code quality the
  second. A prescription at the wrong altitude stops being right the moment the codebase
  differs — which is how the old library got brittle.
- **Writing the item:** checkable — two readers take the same action, and you can tell
  afterwards; one decision per item, an "and" is usually two; give the *why* inline; do not
  restate what a formatter already enforces.
- **Shape:** group by *when it applies*, not by topic. ~20 items is the ceiling; split by
  phase or variant rather than growing one file.
- **Sourcing:** one `Sources:` line per group, naming a checkable authority **with its
  version**. No authority → `Source: reasoned from first principles, <date>`, honestly. Never
  cite what you have not read.
- **Anti-patterns:** aspirational items; unfalsifiable ones ("consider performance"); items
  copied from a framework's docs; a file that only ever grows.

## How each stage runs

1. I implement the stage and commit it.
2. **The `stage-gate-auditor` is dispatched against that stage's gate** — read-only, running
   the checks itself, reporting pass / fail / cannot-verify per criterion with raw output.
3. Its report goes to you with a recommendation, not a decision.
4. You say proceed or stop. A `fail` or a `cannot verify` on any criterion means the stage is
   not done — the fix goes in and the auditor runs again.

The auditor's report is a second opinion, not an authority. It exists because the agent that
did the work is the worst possible judge of whether the work is finished, and this plan
already caught that exact pattern once in the design itself.

## Summary of stopping points

| After | You have | Complexity vs today |
|---|---|---|
| **Stage 1** | Drag removed, safety net added, rules intact | **Lower** |
| **Stage 3** | New simpler library, tested, no automation | About the same |
| **Stage 5** | Automation over hand-curated rules, no self-modification | Higher, capability gained |
| **Stage 7** | The full design | Higher, with a self-editing loop |

Each gate is a real decision, not a formality. The plan is written so that stopping is a
legitimate outcome at A, B or C rather than an abandoned migration.
