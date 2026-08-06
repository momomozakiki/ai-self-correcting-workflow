# Align workflow-core with the Claude Code layout guide

## Context

Work had started on a checklist implementation before settling how this repo's Claude Code
configuration is laid out and how its own process relates to Claude Code's runtime. This plan
stops that and does the structural pass first.

The trigger is an external document, *"Claude Code: The Definitive Guide to File, Folder
Structure, and Actual Workflow" v6.0 (2026-08-06)*, which the user has designated the project's
golden rule.

**What research established before planning** — all three verified, not assumed (live docs
fetched 2026-08-06 from `code.claude.com/docs/en/claude-directory` and `/hooks`):

1. **Neither document is current with the runtime.** The guide is v6.0 dated 2026-08-06 but
   cites source docs dated 2026-07-16 → 2026-07-29. The repo's `claude-code-layout` skill and
   `tests/test_claude_layout.py` are stamped "verified 2026-08-06 against **v2.1.221**".
   The installed runtime is **v2.1.223** (two extensions present:
   `anthropic.claude-code-2.1.221-win32-x64` and `-2.1.223-win32-x64`), so the repo's stamp is
   one version stale and nothing detected it. Same document date; what distinguishes the repo
   is *correctness*, not recency — see 2.

2. **The guide contains errors confirmed against the live docs.** Verbatim from the docs'
   "Exit code 2 behavior per event" table: `Stop` → "Yes | Prevents Claude from stopping,
   continues the conversation"; `SubagentStop` → "Yes | Prevents the subagent from stopping";
   `PreCompact` → "Yes | Blocks compaction"; `PostToolBatch` → "Yes | Stops the agentic loop
   before the next model call". The guide's Part 5.3 table marks all of these non-blocking.
   The docs' Decision-control table specifies the shape `decision: "block"`, `reason` — exactly
   what [workflow_hook.py:1228](hooks/workflow_hook.py#L1228) emits, so the claim is falsified
   by running code as well as by the docs.
   The guide's table lists **24** events; the live docs list **31**, omitting `DirectoryAdded`,
   `WorktreeRemove`, `PreCompact`, `PostCompact`, `Elicitation`, `ElicitationResult`,
   `SessionEnd` — all 31 of which `tests/test_claude_layout.py:73-82` already has correct.
   The guide is also internally inconsistent: its v6.0 changelog claims it "added `PreCompact`
   and `PostCompact` to hook events", but neither appears in its table.
   Finally its "exit 2 blocks (PreToolUse only)" line is wrong — exit 2 is the general
   cross-event blocking path, and exit 1 is *non-blocking*, not "error but continue".

3. **The hook script is not misplaced.** The guide itself (Part 5.1, Part 8) and the live docs
   agree hook scripts are *registered, not discovered*; `.claude/hooks/` is organizational only.
   `hooks/workflow_hook.py` is correctly registered and firing.

The user reviewed points 2 and 3 and elected to move the hook anyway and to adopt the guide as
golden rule. Both decisions are honoured below. The one adjustment: the guide is adopted as the
repo's golden-rule **document**, carrying a dated v6.1 errata for the three corrections above —
a golden rule that is wrong about its own subject cannot function as one, and the erroneous
table cannot be encoded into `tests/test_claude_layout.py` without the suite failing against
the repo's own working `Stop` hook.

**Intended outcome:** hook under `.claude/hooks/`, the guide vendored with provenance and
errata, a layout-auditor subagent, a machine-checked doc-revalidation convention, CLAUDE.md
split into `.claude/rules/`, and a written assessment of the 27 unused hook events.

---

## Workflow phase framing

This is a `new_module`-sized change under the Adaptive Self-Correcting Workflow. Phase 0 (F1
git sync, F2 env, F3 living docs, F4 roadmap) runs first. Every stage below logs to
`history/2026-W32.md`. Closure archives to `plans/archive/`.

Stages 1 and 2 must each land as **one commit** — a partial hook move leaves the Tier-0 guard
unreachable while four governance artifacts still claim `live`.

---

## Stage 0 — Codify "settle disputes by direct test"

This stage exists because of how this very plan went: two claims were disputed, and reciting
documentation at each other settled nothing. Executing the hook settled it in one command.
That is now a rule, not a habit.

**The rule, in two parts:**

1. **When a factual claim about system behaviour is disputed or uncertain, run it — don't
   argue it.** Cite docs only to *design* the test, never in place of one. Test **every**
   competing claim, not just the one you expect to win. If a claim genuinely cannot be tested,
   say so explicitly and label it unproven rather than settling for the strongest argument.
2. **When a test needs the user, write the instructions in plain language.** Assume no
   expertise. Give the exact thing to type or click, say what a pass looks like and what a
   failure looks like, and state why it can't be done without them. No jargon, no
   "simply run X", no assuming they know what a hook or a stdin payload is.

**Where it goes** — the repo's codification pattern from `CLAUDE.md` is *rule file + a line in
the skill*, mirrored:

- `.ai/01-phases/rule-direct-test-disputes.json` — full artifact schema (`id`, `version`,
  `tier`, `workflow_phase`, `condition`, `rule`, `ai_action`, `checklist`).
  `enforcement_status: "convention"` with an honest `enforcement_note`: **nothing can enforce
  "you ran the test"** — no hook sees the difference between a tested claim and a confident
  one. Per `CLAUDE.md`, a convention rule must say what is missing rather than imply a guard.
- `.ai/01-phases/manifest.json` — register it.
- **`GUIDE.md` §12** — `tests/test_governance_library.py::StepMapping` compares the §12 step
  table against `01-phases/manifest.json`. Adding a rule without a §12 row **fails the suite**.
  This is the trap in this stage.
- `templates/ai-library/01-phases/` — byte-for-byte mirror; `TemplateParity` enforces it.
- A line in [adaptive-workflow/SKILL.md](.claude/skills/adaptive-workflow/SKILL.md) Phase 2
  execution guards, alongside the existing reversibility / loop / heredoc guards — it is the
  same kind of rule. Mirror to `templates/skills/`.
- `.claude/rules/` (Stage 5) — the communication half belongs where it loads every session.

**Sourcing honesty:** `ChecklistItems` requires every item to cite a `source` with an authority
level. The source here is a project decision made in this session, not an external standard —
it must be recorded as such, with the ledger entry as the reference. Do not dress an internal
decision up as an industry citation to satisfy the validator.

**Applied immediately:** Verification step 8 below is the outstanding untested claim from this
plan, and Stage 2's re-verification against v2.1.223 is the same rule applied to stale stamps.

---

## Stage 1 — Move the hook to `.claude/hooks/`

`git mv hooks/workflow_hook.py .claude/hooks/workflow_hook.py`. **No change to the script
itself**: [workflow_hook.py:48-74](hooks/workflow_hook.py#L48-L74) `find_config_path()` already
walks upward from `__file__` looking for `.claude/workflow_config.json`, so it resolves from the
new location. Verified, not assumed.

Update every referencing site in the same commit:

| File | Change |
|---|---|
| [.claude/settings.json](.claude/settings.json) | 4 hook commands → `$CLAUDE_PROJECT_DIR/.claude/hooks/workflow_hook.py` |
| [.claude/workflow_config.json:9](.claude/workflow_config.json#L9) | `source_directories`: `"hooks"` → `".claude/hooks"` |
| [tests/test_hook.py:29-31](tests/test_hook.py#L29-L31) | `sys.path.insert` → `REPO_ROOT / ".claude" / "hooks"` |
| [tests/test_governance_library.py:887-891](tests/test_governance_library.py#L887-L891) | `SettingsWiring.CONFIGS` expected substrings, both entries |
| [tests/test_claude_layout.py:61](tests/test_claude_layout.py#L61) | comment referencing the old path |
| [.github/workflows/tests.yml:30](.github/workflows/tests.yml#L30) | `python .claude/hooks/workflow_hook.py --self-test` |
| `templates/settings.json.hooks`, `templates/CLAUDE.md.fragment` | adopter path (see below) |
| `.ai/01-phases/*.json`, `.ai/02-market-rules/prohibitions/*.json` | 12 rules' `enforced_by` `path::symbol` values |
| `templates/ai-library/**` | byte-for-byte mirror of the above — `TemplateParity` enforces it |
| `schemas/hook_contract.md`, `schemas/config_schema.json` | path references |
| `CLAUDE.md`, `README.md`, `GUIDE.md` (§2, §7, §8), `ROADMAP.md`, `CHANGELOG.md`, `GUIDE_CHANGELOG.md`, `.ai/README.md`, `.ai/GROWTH.md`, `docs/*` | prose references |

**Do not rewrite `history/*.md`.** Ledger entries record what was true when written; editing
them falsifies the record. The move gets a *new* entry noting the old path.

**The adopter-path consequence, stated plainly:** adopters vendor workflow-core at
`.claude/workflow-core/`, so the dispatcher's path becomes
`.claude/workflow-core/.claude/hooks/workflow_hook.py`. This nesting is the cost of the move
and must be applied consistently to `templates/settings.json.hooks` (4 sites) and
`templates/CLAUDE.md.fragment`, or every adopter's guard silently stops firing.

Also extend [tests/test_claude_layout.py:251](tests/test_claude_layout.py#L251)
`NonStandardFiles` — it currently only inspects `p.is_file()`, so a new directory under
`.claude/` is unchecked. Add a `STANDARD_CLAUDE_DIRS` allowlist (`skills`, `agents`, `commands`,
`rules`, `workflows`, `output-styles`, `agent-memory`, `hooks`) so `.claude/hooks/` is a
declared choice and a stray directory is caught.

### Existing adopters will silently break — migration is required

Verified: `git tag | wc -l` = **0**. There is no release mechanism; adopters track this repo as
a submodule at `.claude/workflow-core/` and own their `.claude/settings.json`, which they
merged from `templates/settings.json.hooks` at adoption time. Pulling the submodule updates the
script's location but **not their settings.json**. Their `PreToolUse` command keeps naming
`.claude/workflow-core/hooks/workflow_hook.py`, which no longer exists.

Failure mode: the command is not found, the hook fails, and the dispatcher **fails open by
design** (GUIDE §7.5). No error surfaces. Four `.ai/` artifacts continue to declare `live`
while nothing enforces them — precisely the defect `SettingsWiring` was written to catch, but
in the adopter's repo where our tests do not run.

Required in Stage 1:
- `CHANGELOG.md` entry marked **BREAKING**, with the literal before/after command string to
  find and replace.
- The same notice in `templates/CLAUDE.md.fragment` and `README.md`.
- A verification line an adopter can run to confirm their guard still fires — reuse the probe
  proven above: feeding a `PreToolUse` event with `rm -rf history/` must print
  `permissionDecision: "deny"`. Silence means broken.

**Gate:** `python -m unittest discover -s tests` fully green, and
`python .claude/hooks/workflow_hook.py --self-test` exits 0, before committing.

---

## Stage 2 — Adopt the guide as the golden-rule document

Vendor it at `docs/claude-code-layout-guide/index.md` with the repo's doc-standard frontmatter
per [doc-frontmatter.md](.claude/skills/adaptive-workflow/references/doc-frontmatter.md):
`official: true`, `source:` the guide's own reference URLs, `version: 6.1`,
`last_validated: 2026-08-06`.

Body = the guide verbatim, plus:

- A **Corrections** section, dated and sourced, carrying the three findings from Context §2.
  Each states the guide's claim, the live-doc wording, and the observable evidence
  (`Stop` blocking in `handle_stop`).
- A **Provenance** header naming the guide's source docs *and* their July 2026 dates against
  this repo's v2.1.221 verification date, so a future reader can tell which is older.
- A Revision History row: `6.1 | 2026-08-06 | Errata against live docs`.

Then reconcile the two existing artifacts *toward* the guide where it adds material the repo
lacks — `.worktreeinclude`, `/etc/claude-code/CLAUDE.md` in the memory hierarchy, the five hook
types, the orchestrator model (Part 10), `ultracode`:

- [.claude/skills/claude-code-layout/SKILL.md](.claude/skills/claude-code-layout/SKILL.md) —
  add a "Verified <date> against v<version>" line (currently only in the reference file), link
  the vendored guide, and add the orchestrator distinction.
- [references/directory-map.md](.claude/skills/claude-code-layout/references/directory-map.md) —
  add the missing paths; keep its deliberate refusal to inline the hook-event list.

**Re-verify the stale stamps as part of this stage.** Both this skill and
`skill-authoring/references/verified-facts.md` claim v2.1.221; the runtime is v2.1.223. Re-read
the live docs and the [release notes](https://github.com/anthropics/claude-code/releases) for
2.1.222–2.1.223, confirm each claim still holds, and re-stamp to v2.1.223. Per
`verified-facts.md:14-20`, check the **release notes as well as the doc pages** — that file
records a prior wrong entry caused by treating one doc page as the whole record.

**Write the re-stamping procedure down**, in `skill-authoring/SKILL.md`, so it is repeatable
rather than rediscovered: (1) read the installed version from
`ls ~/.vscode/extensions/anthropic.claude-code-*` — take the **highest**, not the first, since
several can coexist; (2) diff the release notes from the stamped version to that one; (3) re-read
each cited doc page; (4) confirm or correct every claim; (5) update the stamp and log the
re-verification in the ledger. This is a **manual** procedure — no automated version check
exists, and inventing one that scrapes release notes would be a new dependency for a
stdlib-only repo.

`tests/test_skills.py::SkillTemplateParity` requires mirroring into `templates/skills/`.

---

## Stage 3 — Layout-auditor subagent

Create `.claude/agents/layout-auditor.md` — the first occupant of `.claude/agents/`, which
also exercises `agent_problems()` in `tests/test_claude_layout.py:168`, currently dead code.

Frontmatter per
[frontmatter-by-type.md](.claude/skills/claude-code-layout/references/frontmatter-by-type.md) —
note `disallowedTools` (camelCase) for agents, *not* the skills spelling:

```yaml
---
name: layout-auditor
description: Audits .claude/ wiring — that every discovered artifact sits where Claude Code
  scans, and every hook script is registered in settings.json.
model: sonnet
disallowedTools: Write, Edit, NotebookEdit
---
```

Read-only by construction: it reports drift, it does not fix it. Its checklist is the
discovered-vs-registered question from the skill, applied to both settings files (repo and
adopter template) — the asymmetry that once shipped adopters an unenforced guard.

---

## Stage 4 — Doc-revalidation protocol + staleness test

The repo already uses `Verified <date> against Claude Code v<version>` in two reference files,
and [skill-authoring/SKILL.md:115](.claude/skills/skill-authoring/SKILL.md#L115) deliberately
forbids doc-standard frontmatter on skills. So: **keep the inline convention, make it
machine-checked** — do not add `version:`/`last_validated:` frontmatter to skills.

- Fix the exact line format and document it in `skill-authoring/SKILL.md`.
- Add `tests/test_skills.py::VerificationStamps`: every skill reference file asserting
  Claude Code behaviour carries a parseable stamp, and the date is within
  `revalidation_interval_days` (the existing config key,
  [config_schema.json:57](schemas/config_schema.json#L57), default 180). Follow the file's
  existing `NegativeControls` pattern — a mutation test proving the check catches its own
  regression.
- Extend `run_self_test()` to report stale stamps alongside the existing missing-frontmatter
  report. **Reported, never enforced**, matching how maturity level is handled.

**Evidence this stage is needed, not speculative:** the v2.1.221 stamps were written 2026-08-06
and were already behind the installed v2.1.223 runtime when this plan was written. 238 tests
passed throughout. A date that goes stale with nothing observing it is the exact failure mode
[claude-code-layout/SKILL.md:15](.claude/skills/claude-code-layout/SKILL.md#L15) names —
"If this silently stopped being read, what would I observe?" Currently: nothing.

---

## Stage 5 — Split CLAUDE.md into `.claude/rules/`

**Measured: CLAUDE.md is 93 lines** — less than half the guide's ~200-line splitting threshold
("When CLAUDE.md approaches 200 lines, start splitting into rules", live docs,
`/docs/en/claude-directory`). So this stage is *purely pre-emptive*; it buys structure, not
relief from a real problem, and it is the one stage I would drop if scope needs cutting. It is
included because you selected it. Move the stable, topic-scoped material out and leave
CLAUDE.md as orientation plus Tier 0:

- `.claude/rules/workflow-phases.md` — Phase 0–3 discipline
- `.claude/rules/governance-library.md` — `.ai/` enforcement_status rules, mirror requirement
- `.claude/rules/claude-code-layout.md` — `paths: [".claude/**"]` frontmatter, so it loads only
  when touching configuration

Tier 0 prohibitions **stay in CLAUDE.md**. Evidence, from `/docs/en/memory`, verbatim:

> Nested CLAUDE.md files in subdirectories and rules with `paths:` frontmatter are not
> re-injected automatically; they reload the next time Claude reads a file in that subdirectory
> or a file matching the rule's patterns.

So a `paths:`-gated rule **silently disappears after `/compact`** until a matching file is read.
Anything that must hold unconditionally — Tier 0, and the Stage 0 direct-test rule — must be
ungated. Only `claude-code-layout.md` carries `paths:`, because it is genuinely only relevant
when touching configuration, and its absence after compaction is harmless.

**`paths:` well-formed criteria** — defined from the docs, not invented:

| Criterion | Source |
|---|---|
| YAML **list of strings**, not a bare string | doc example: `paths:` then `- "src/api/**/*.ts"` |
| Glob patterns; brace expansion allowed | `src/**/*.{ts,tsx}` documented |
| Non-empty list (omit the field instead of an empty list) | "Rules without a `paths` field are loaded unconditionally" |
| Balanced `[` — an unreadable bracket expression matches **nothing** | "A pattern with a `[` that can't be read as a bracket expression … matches nothing"; escape as `\[` |
| Brace expansion budget: ≤1,000 expanded patterns per rule | "a rule's whole `paths` list shares one budget of 1,000 expanded patterns and 4 MiB" |

The test asserts these five. The bracket rule is the valuable one — an invalid pattern fails
silently, matching no files, which is exactly this repo's recurring defect class.

**Adopters need these rules too.** `templates/` currently has `skills/`, `ai-library/`, `docs/`,
`history/` — verified, **no `rules/`**. Stage 5 must add `templates/rules/` plus a parity test
modelled on `SkillTemplateParity`, or adopters get the split CLAUDE.md with the rules missing.

`tests/test_claude_layout.py` already lists `rules` in `DISCOVERED_DIRS`. Note rules are
discovered **recursively** ("All `.md` files are discovered recursively"), so the layout test's
nesting assumptions need checking against that.

**`GUIDE.md` §2.1 and §2.2** must be updated to show `.claude/rules/` in both the workflow-core
tree and the post-adoption tree.

---

## Stage 6 — Assessment of unused hook events (write-up only, no wiring)

The dispatcher implements 4 of 31 events. Produce
`docs/hook-event-assessment.md` (doc frontmatter, `official: false`) evaluating, against the
live docs and the repo's fail-open posture:

- `SessionEnd` / `PreCompact` — could make the `plans/UNFINISHED.md` breadcrumb survive a
  compaction, not just a `Stop`. Most likely genuine win.
- `SubagentStop` / `TaskCompleted` — ledger prompts for delegated work the `Stop` hook cannot see.
- `UserPromptSubmit` — blocking; note the risk of a fail-open hook gaining a blocking path.
- `PermissionDenied` — observability for guard hits.
- Why `FileChanged` remains unsuitable (weekly-rolling ledger filename vs literal matcher) —
  already reasoned in GUIDE §7.3; carry it forward.

Each entry: recommendation, cost, and what would have to be true to adopt it. Feed accepted
items to `ROADMAP.md`; **wire nothing in this pass.**

---

## Not doing

**Not starting a new repository.** Everything structural is already compliant or a rename away;
a fresh repo discards 4 test suites (~3,300 lines), the `.ai/` governance library, and the
ledger — with no defect that a new repo would fix.

**Not replacing the Adaptive Self-Correcting Workflow with "the Claude workflow."** They are
different layers, not alternatives: Claude Code's Think→Act→Observe loop is the *runtime*; the
Adaptive workflow is *process governance* (ledger, provenance, closure) layered on it via hooks.
The guide describes no process that could replace Phase 0–3. Stages 3, 5 and 6 are the real
content of "use more of the platform." This reasoning gets recorded in
`docs/governance-integration-decision.md`.

---

## Verification

Per stage:

1. `python -m unittest discover -s tests` — green after **every** stage. **Measured baseline:
   238 tests, all passing, 8.6s** (run 2026-08-06 before any change). Any stage ending below
   238 passing has regressed something.
2. `python .claude/hooks/workflow_hook.py --self-test` — exit 0, maturity level unchanged or up.

End-to-end, after Stage 3 — observation, not inspection, per the skill's own rule:

3. **Guard still fires from the new path:** in a scratch clone, attempt a protected-path
   deletion (`rm -rf history/`) and confirm the hook returns `permissionDecision: "deny"`.
   This is the single most important check — it proves the move preserved the wiring.
4. **Skill loads:** `/reload-skills`, then confirm `claude-code-layout` is listed.
5. **Subagent loads:** confirm `layout-auditor` appears in the subagent listing and can be
   spawned. This is the only proof `.claude/agents/` is wired.
6. **Rules load:** new session; confirm `.claude/rules/*.md` content is in context, and that
   the `paths:`-gated rule loads only after a `.claude/` file is read.
7. **SessionStart context** still renders (branch, env check, roadmap next action).
8. **The one test that needs you** — settles the guide's `Stop` claim end-to-end.
   Written per the Stage 0 plain-language rule.

   **What we're finding out:** the guide says Claude Code ignores a "stop" signal from our
   script. We've proved our script *sends* the signal. We have not proved Claude Code *listens*
   to it. Only you can check this, because it needs a real conversation to end — I can't end my
   own turn and watch what happens at the same time.

   **What to do:**
   1. I'll change one file and deliberately not write the history note that our rules require.
   2. You then just... let me finish my reply. Don't type anything yet.
   3. Watch what happens next.

   **What you should see if the guide is WRONG (and we are right):** I won't stop cleanly.
   A message appears saying source files changed but the history note is missing, and I keep
   going instead of handing back to you.

   **What you should see if the guide is RIGHT:** nothing unusual. My reply just ends and it's
   your turn, with no warning message.

   **Either result is useful** — tell me which one you saw. If it's the second, the guide is
   correct on this point and I'll correct the plan rather than defend it.

   Run this **before** the Stage 1 move and **again after**, so if behaviour changes we know it
   was the move that changed it and not something else.

Closure: ledger entry per stage in `history/2026-W32.md`, `ROADMAP.md` updated,
`plans/UNFINISHED.md` cleared, pushed.

**`plans/archive/` does not exist yet** — verified, `plans/` contains only `HANDOVER.md`. It
must be created during closure, at `plans/archive/2026-08-06_claude-layout-alignment/plan.md`.
Note the ordering trap: `plans/archive` is in `tier0_guard.protected_paths`, so once created it
is guard-protected against deletion. Create it, don't experiment inside it.

**Skill↔guide drift check.** The vendored guide (`docs/claude-code-layout-guide/`) and the
`claude-code-layout` skill both assert Claude Code behaviour and can diverge. Comparing their
prose automatically is not implementable and would be a brittle test. What *is* checkable, and
what will be tested: **both must name the same Claude Code version in their verification
stamp.** That catches the realistic drift — one re-verified, the other forgotten — without
pretending to diff English.

---

## Evidence log

Every load-bearing claim in this plan, and how it was checked on 2026-08-06. Nothing here is
inferred from memory.

| Claim | How verified | Result |
|---|---|---|
| `Stop` can block | Live docs, "Exit code 2 behavior per event" table | "Yes — Prevents Claude from stopping" |
| **Repo's `Stop` hook actually emits a block** | **Executed the hook: `PostToolUse` (seed) → `Stop`** | **`{"decision": "block", "reason": "Source files changed … ledger … wasn't updated"}`** |
| **Tier-0 guard actually denies** | **Executed `PreToolUse` with `rm -rf history/`** | **`permissionDecision: "deny"`, prohibition-delete-ledger** |
| **Force-push guard actually denies** | **Executed `PreToolUse` with `git push --force origin main`** | **`permissionDecision: "deny"`, prohibition-force-push-shared** |
| Claude Code *honors* Stop blocks | `stop_hook_active` is set **by the platform** on re-invocation; `max_blocks: 2` caps repeats. Tests `test_stop_hook_active_short_circuits`, `test_max_blocks_cap` pass | Indirect but strong — an ignored block needs no cap and would never set the flag. **Not yet observed end-to-end; see Verification step 8** |
| Guide lists 24 events, docs list 31 | Counted guide Part 5.3 vs fetched `/docs/en/hooks` | 7 missing from guide |
| Repo's event list is correct | Read `tests/test_claude_layout.py:73-82` | All 31 present |
| Hook scripts are registered, not discovered | Fetched `/docs/en/claude-directory` file tree | No `hooks/` entry in the tree |
| Moving the hook needs no code change | Read `find_config_path()` at `workflow_hook.py:48-74` | Walks upward for `.claude/workflow_config.json` |
| Runtime version | `ls ~/.vscode/extensions/anthropic.claude-code-*` | 2.1.221 **and** 2.1.223 installed |
| CLAUDE.md length | `wc -l CLAUDE.md` | 93 lines |
| Test baseline | `python -m unittest discover -s tests` | 238 passed, 8.6s |
| `.claude/hooks/` dir won't trip layout test | Read `NonStandardFiles` at `test_claude_layout.py:257-260` | Filters `p.is_file()`; dirs unchecked → gap to close |

Two estimates in an earlier draft were wrong and are corrected above: CLAUDE.md is 93 lines,
not ~150; the suite is 238 tests, not "~30+".
