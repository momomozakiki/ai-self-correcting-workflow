---
title: Retrospective — mistakes, root causes, and what they became
version: 1.3
last_validated: 2026-08-05
official: true
source: agent-generated
tags: [retrospective, self-hardening, mistakes, governance]
applies_when: "Closing a task (Phase 3), or checking whether a mistake has happened before."
estimated_tokens: 900
---

# Retrospective
**Version 1.0** — *The self-hardening loop's input. A mistake recorded twice becomes structure.*

## Revision History
| Version | Date       | Change   |
|---------|------------|----------|
| 1.0     | 2026-08-04 | Initial, seeded with two real mistakes from the v14 integration session. |
| 1.1     | 2026-08-05 | New entry: an `ask` tier enforces the prompt, not the outcome — demonstrated within an hour of the Tier-0 guard shipping, and the cause of the Stop-hook false positive alongside it. |
| 1.2     | 2026-08-05 | New entry: an instrument that manufactures the state it reports — the breadcrumb loop and the maturity ladder's masking, both correct by their own logic and both misleading. |
| 1.3     | 2026-08-05 | Two entries. A standing caveat nobody tried to resolve (the CLI version, recoverable from the install path across two sessions) — **recurring**, and it owes a rule. And a negative control that proved nothing twice, because its baseline was already red and then because the control itself dirtied the tree. |

---

## How to use this file

Log a mistake when it costs time or produces a wrong result — not every stumble. One `###`
heading per mistake.

- **First occurrence**: write it up. That's all.
- **Second occurrence**: append `(recurring)` to the heading. It now owes a rule.
- **Codified**: once the rule exists, add a `**Codified:**` line naming it.

`python .claude/hooks/workflow_hook.py --self-test` reports any `(recurring)` entry that still has
no `**Codified:**` line, and withholds maturity level 5 until none are outstanding. The
threshold is deliberately two: one mistake is noise, two is a pattern worth paying for.

---

### 2026-08-04 — Heredoc-fed stdin mangles escape sequences (recurring)

- **What:** Patching `.claude/hooks/workflow_hook.py` via `python - <<'PY' ... PY` corrupted the
  script: `\\n` inside the Python source arrived as a real newline, so every replacement
  pattern containing an escape failed to match.
- **Why it matters:** The failure is silent until a pattern misses. Worse, a partial match
  would have written a half-patched file.
- **Root cause:** Feeding a program to an interpreter over heredoc stdin puts the shell
  between you and your source. Quoting the delimiter (`<<'PY'`) suppresses *variable*
  expansion but is not a guarantee across shells and tool layers.
- **Why this is recurring:** The same root cause was already documented once, for
  `git commit -F -` and heredoc commit messages (GUIDE §4 Phase 3, v4.6). This is the second
  manifestation, so the guidance is generalised rather than left as a git-specific caveat.
- **Fix:** Write the script to a file and run the file. For edits to tracked source, prefer
  the editing tools over generated patch scripts entirely.
- **Codified:** `.ai/01-phases/rule-no-heredoc-stdin.json`; GUIDE §4 Phase 2; SKILL.md Phase 2.

### 2026-08-05 — A governance library that nothing checked drifted in one commit

- **What:** The v14 integration shipped `.ai/` with an `enforcement_status` on every
  artifact and the rule that none may imply enforcement it lacks. Nothing tested any of
  it. An audit one commit later found seven distinct drifts: an invented `risk_source`,
  six out-of-band weights, an enum documented wrong in `GROWTH.md`, ten `live` claims with
  nothing to point at, a v14 step mapping whose tier contradicted the GUIDE, four
  prohibitions missing the `provenance` the README promised, and a ledger slug list
  mislabelled as the CISA taxonomy.
- **Why it matters:** Every artifact read as correct. That is the failure mode — prose
  that describes a control is indistinguishable from a control until something tries to
  break it. The integration commit even said "no artifact may imply enforcement it does
  not have" while shipping ten artifacts that did exactly that.
- **Root cause:** Writing the rule and the artifacts in one pass, with no adversarial step
  between them. The library was reviewed for whether it read honestly, not for whether it
  *was* honest.
- **Fix:** `tests/test_governance_library.py`. A `live` tier now needs an `enforced_by`
  list resolving to real functions and tests; a `convention` needs an `enforcement_note`
  naming the real mechanism. Confirmed by running the tests against the unfixed library
  first — 42 failures — rather than writing them until they passed.
- **Codified:** not yet — first occurrence. If governance artifacts drift again without a
  test catching them, this becomes a rule: *an artifact that asserts a property about the
  codebase ships with the test that checks it, in the same commit.*

### 2026-08-05 — Nudging a number to clear a threshold (caught in review)

- **What:** The first draft of the fix above proposed raising `rule-closure`'s
  `risk_weight` from 7 to 8, and lowering `rule-lint-test`'s from 7 to 6, so they would sit
  inside their taxonomy bands. Review asked what the justification for the change was. The
  honest answer was that there wasn't one — the numbers were being moved to make a check
  pass.
- **Why it matters:** This is the same failure as a faked `live` tier, wearing different
  clothes: an honest assessment bent until it satisfies a validator. It nearly shipped
  *inside the change whose entire purpose was to stop that*, which is what makes it worth
  recording. A test that can be satisfied by adjusting the data it measures is not a test.
- **Root cause:** Treating an imported band as ground truth. The CISA bands were written
  for an agent fleet; some do not transfer to a single-operator repo, and the mismatch was
  information about the band, not an error in the weight.
- **Fix:** Zero weights were changed. `risk_weight_note` records why a band does not fit,
  and the test accepts an out-of-band weight only with one attached — and rejects a note on
  an in-band weight, so it cannot decay into boilerplate. Rationale in
  `docs/governance-integration-decision.md` §7.
- **Codified:** not yet — first occurrence. If a second "adjust the data to satisfy the
  check" instance appears, this becomes a rule: *when data fails a validator, fix the data
  only if the data is wrong; otherwise fix the validator or record the exception.*

### 2026-08-05 — An instrument that manufactures the state it reports

- **What:** The Stop hook writes `plans/UNFINISHED.md` when the tree is dirty. That file is
  itself untracked, so the next Stop saw it in `git status --porcelain` and counted it as
  more unfinished work — which kept the tree dirty, which rewrote the breadcrumb. The loop
  could not clear on its own. Separately, `--self-test` reported "level 2/5 (Repeatable)"
  while seven of nine checks passed: the maturity ladder `break`s at the first failed gate,
  so one warn at level 3 hid every passing check at levels 4 and 5.
- **Why it matters:** Both were *correct* by their own logic and both told the reader
  something false. A reminder that fires on a state the user considers normal gets
  dismissed, and once dismissed it is dismissed for the real cases too. A maturity number
  that reads "immature" when one box is unticked invites either panic or, worse, the habit
  of ignoring it.
- **Root cause:** Designing each check in isolation and never asking what it looks like
  *after* it fires. The breadcrumb's side effect on the next session was invisible from
  inside a single session; the ladder's masking only appears once a low gate actually
  fails, which took months to happen.
- **Fix:** `dirty_excluding_breadcrumb` and `has_outstanding_plan` ignore the hook's own
  marked breadcrumb while still honouring a human-authored plan at the same path; the
  maturity report names the blocking gate and what already passes above it. Verified across
  *two* Stop events, since a single-shot test could not have seen the loop.
- **Codified:** not yet — first occurrence of this specific shape. If a third instrument is
  found reporting something other than the truth, this becomes a rule: *a check ships with
  a test for what it does on the run after it fires, not only on the run that trips it.*

### 2026-08-05 — An `ask` tier enforces the prompt, not the outcome

- **What:** Within an hour of the Tier-0 guard shipping, `guard_heredoc` escalated a
  heredoc via `permissionDecision: "ask"`, exactly as designed. The prompt was approved
  and the heredoc ran. The rule was broken anyway — and the heredoc was how the ledger
  got appended, which is precisely why the `ledger_touched` flag never fired and the Stop
  hook then nagged twice about an entry that was already committed and pushed. One waved
  prompt produced both defects.
- **Why it matters:** `GUIDE.md` §13 defines `live` as *"breaking it produces a visible
  signal"*. That sentence is true of an `ask` and still oversells it. A signal waved
  through is a signal nobody acted on, so `deny` and `ask` are not the same promise while
  the tier vocabulary called them the same thing. Four artifacts carried `live` on the
  strength of an `ask`.
- **Root cause:** Designing the guard around whether the *mechanism* could fire, not
  around whether the *outcome* was guaranteed. `ask` was chosen deliberately and for good
  reasons — a hard block on heredocs was judged worse — but the tier that described it
  did not carry the distinction, so a reader could not tell which artifacts were
  unbypassable and which merely prompted.
- **Fix:** An `enforcement_mode` field (`deny` / `ask`) on every guard-backed artifact,
  bound to the code by `tests/test_hook.py::TestEnforcementModeMatchesGuard`: it feeds
  each guard a command that must trip it and asserts the returned decision equals the
  declared mode. Declaring `deny` on a guard that only asks fails the build. Documented
  in `GUIDE.md` §13 and `.ai/README.md`.
- **A note on the heredoc itself:** this was its third occurrence, and it is already
  codified (see above). A third instance of a codified rule does not owe a new rule — it
  says the codification is not sticking. That is the observation, and it is why the fix
  here is structural rather than another line of guidance.
- **Codified:** not yet — first occurrence of *this* lesson. If a second `ask`-mode
  control is waved through and causes a downstream failure, this becomes a rule: *an
  `ask`-mode control may not be the only enforcement of a Tier-0 prohibition.*

### 2026-08-04 — An environment check that could never pass

- **What:** Added `claude` to `env_check.tool_paths` so `SessionStart` would report the CLI
  version (the `opus` alias needs v2.1.219+). The CLI isn't on `PATH` in this environment —
  Claude Code runs as a VS Code extension — so every session would have reported
  `claude: NOT FOUND`.
- **Why it matters:** A check that always fails trains the reader to ignore the whole block.
  A false negative is worse than no check, because it costs attention on every session and
  eventually devalues the true negatives sitting next to it.
- **Root cause:** Adding the check without first verifying the probe could succeed here.
- **Fix:** Removed the entry. The version guidance is printed unconditionally as a note in
  `--self-test`, where it is accurate without pretending to have measured anything.
- **Codified:** not yet — first occurrence. If a second unverifiable check appears, this
  becomes a rule: *never add a health check without observing it pass and fail.*

### 2026-08-05 — A standing caveat nobody tried to resolve (recurring)

- **What:** "This environment cannot report its own Claude Code version" was written into
  `docs/governance-integration-decision.md` §10 as one of three confounders keeping the
  `FileChanged` probe inconclusive, and into `plans/HANDOVER.md` as an open item for the
  user. It was asked of the user twice. The version was in the extension directory name —
  `~/.vscode/extensions/anthropic.claude-code-2.1.221-win32-x64` — the entire time. One
  directory listing.
- **Why it matters:** The unresolved caveat was doing real work: it kept a probe
  inconclusive and left two version gates open. Worse, it was *correct* — the CLI genuinely
  is not on `PATH` — which is what let it survive. A caveat that is true about the method
  tried reads exactly like a caveat that is true about the question, and only the second
  deserves to stand.
- **Root cause:** The previous entry's conclusion — "the CLI isn't on `PATH` here" — was
  reused as though it settled the *question* rather than one *approach* to it. Once written
  down, it was cited rather than retested. Asking the user is the most expensive fallback
  and it was reached first.
- **Fix:** Version read from the install path; `§10`'s confounder list cut from three to
  two; `--self-test` now prints where to find the version when `claude` is not on `PATH`,
  so the next reader does not repeat the search.
- **Codified:** **yes — this is the second occurrence of the same shape.** The
  2026-08-04 entry above added a check that could never pass; this one kept a caveat that
  never needed to stand. Both are claims about the environment adopted without a probe.
  The rule, now in `.ai/03-planning/rule-verification-planning-review.json` as `VER-PLN-02`
  and in the GROWTH.md sourcing rule: **a claim that something cannot be determined is
  itself a claim, and needs one attempt at determining it before it is recorded.** Escalating
  to the user counts as an attempt only after the local ones are exhausted.

### 2026-08-05 — A negative control that proved nothing, twice

- **What:** Building `.ai/03-planning/`, the control broke a rule file eight ways and
  reported "8/8 caught". Both halves were false. The **baseline was already failing** (13
  failures from an in-flight mirror), so every run reported `FAILED` regardless. Fixed
  that, and it was still wrong: the control's own `.bak` sat inside `.ai/`, and writing a
  broken file diverged `.ai/` from `templates/`, so **`TemplateParity` failed on every
  breakage** whether or not the intended check fired.
- **Why it matters:** A negative control exists to answer "does this test catch this
  defect". A pass/fail count answers "is anything red", which is a different question that
  looks identical in the output. The first version would have shipped a folder whose
  invariants were unverified, with evidence appearing to say otherwise — the precise
  failure this repo exists to prevent, inside the instrument built to prevent it.
- **Root cause:** Counting failures instead of naming them. A count cannot distinguish
  "the check I wrote caught it" from "something unrelated was already broken".
- **Fix:** The control now asserts the **name** of the test that must catch each breakage,
  requires a green baseline and says so loudly when it is not, keeps its backup outside
  `.ai/`, and mirrors each broken file into `templates/` so parity noise cannot masquerade
  as a catch. Result: 14/14, each attributed to the check that should catch it. Two
  breakages were reattributed in the process — they tripped the manifest-agreement check
  before reaching the phase check, which is correct layering the first version would have
  mislabelled as success.
- **Codified:** not yet — first occurrence of *this* lesson. If a second control reports a
  count rather than an attribution, it becomes a rule: *a negative control names the test,
  or it is not a control.*

### 2026-08-06 — The skills were never loaded, and nothing said so

- **What:** The three skills lived in a repo-root `skills/` directory. Claude Code discovers
  skills at `~/.claude/skills/`, the project `.claude/skills/` (plus nested ones below the
  working directory) and plugin directories — **and nowhere else**. So none of them was ever
  a skill: `/adaptive-workflow` did not exist, no description ever triggered an automatic
  load, and the `disallowed-tools: AskUserQuestion` on `autonomous-task` — the field whose
  entire job is to physically remove the tool — was inert for its whole life. They appeared
  to work only because `CLAUDE.md` named their file paths in prose, so the agent read them
  as ordinary files.
- **Why it matters:** This is the repository's own stated failure mode, in the repository
  itself: **enforcement claimed and not present**. `CLAUDE.md` requires `live` artifacts to
  name real enforcing code and forbids implying enforcement that does not exist. A
  frontmatter field in an undiscovered directory is precisely that — a control that reads as
  binding, cannot bind, and reports nothing either way. The governance library was audited
  to five decimal places while the mechanism delivering it was disconnected.
- **Root cause:** The location was never verified against the documentation, because
  nothing about it looked like a claim. `skills/` at the repo root is a reasonable-looking
  directory, and every artifact inside it was correct. The defect was in the one property
  no test covered and no reviewer would think to check — *whether the runtime can see it at
  all*.
- **Fix:** Moved to `.claude/skills/`; `tests/test_skills.py` now fails if the old path
  reappears anywhere outside the append-only records, and checks the properties that
  otherwise fail silently (entrypoint casing, unknown frontmatter keys, the 500-line cap,
  the ~5,000-token compaction budget, link resolution, adopter-template parity). Harvested
  into `.ai/05-domains/rule-skill-authoring-review.json` per GROWTH.md, and into the
  `skill-authoring` skill.
- **Codified:** yes — `.ai/05-domains/rule-skill-authoring-review.json` (`SKA-LOC-01`) and
  `tests/test_skills.py::SkillStructure`.
- **The general lesson, which is larger than skills:** *an artifact's correctness is not its
  effectiveness.* Every check in this repository asked whether the content was right. None
  asked whether anything was reading it. For each control here that is claimed to be live,
  the question "what would I observe if it silently stopped running?" has to have an answer
  — and if the answer is "nothing", that is the finding.

### 2026-08-06 — The guard we shipped to other people was never wired (recurring)

- **What:** `templates/settings.json.hooks`, the fragment adopters merge into their
  `.claude/settings.json`, had no `PreToolUse` block and no `defaultMode`. `PreToolUse` is
  the only event the Tier-0 guard runs on. So in **every adopting project**, force-pushing a
  protected branch was not denied, deleting `history/` or `plans/archive/` was not denied,
  and history rewrites and heredocs never asked — while `CLAUDE.md`, `GUIDE.md` §7 and four
  `.ai/02-market-rules/prohibitions/*.json` files all declared those prohibitions `live`,
  with `enforced_by` naming real `guard_*` symbols. Measured: **0 of 3** Tier-0 probes denied
  under the template, 3 of 3 under this repo's own settings.
- **Why it matters:** this is the skills defect one layer out, and worse in two ways. It is
  security-adjacent, and it travels — the repository that wrote the rule was the only place
  the rule worked. Everyone who trusted the documentation got nothing.
- **Root cause:** `SettingsWiring` read `.claude/settings.json` and nothing else. Its own
  docstring said so — *"a file no other test reads"* — which was written as a justification
  for the class existing, and was simultaneously an exact description of the hole. **We
  tested the copy we use, not the copy we ship.** `EnforcementHonesty` then passed for the
  wrong reason: it resolves `enforced_by` to real symbols, and a symbol can be real and
  unreachable at the same time.
- **Fix:** the template carries the `PreToolUse` block and `defaultMode`; `SettingsWiring`
  runs its four assertions over both configs with a per-config expected dispatcher path;
  `test_claude_layout.py` independently asserts both files register the same hook events.
  `CHANGELOG.md` carries merge instructions and a verification step for existing installs.
- **Codified:** yes — `tests/test_governance_library.py::SettingsWiring` and
  `tests/test_claude_layout.py::HookRegistration`.
- **Marked recurring** against the 2026-08-06 skills entry above. Both are the same defect:
  an artifact that is correct and reaches nothing. That is now twice, so per `GROWTH.md` it
  is structure, not a note. **The rule: for anything this repository distributes, the test
  must read the distributed copy.** A test that reads only the dogfooded copy proves the
  dogfooding, not the product.

### 2026-08-06 — A reference page is not the whole record

- **What:** I recorded "no documented minimum version for `disallowed-tools`" in
  `verified-facts.md`, and told the user firmly that stating a floor "would mean inventing
  one". A version floor exists: **v2.1.152, 27 May 2026**, in the release notes. The same
  release added `/reload-skills`, which made the "restart Claude Code" guidance I had
  propagated into four places — including the adopter-facing fragment — stale on arrival.
- **Why it matters:** the user's guide was right and I overrode it with a confident,
  well-argued negative. A recorded absence is harder to dislodge than an open question,
  because it reads as having been checked.
- **Root cause:** I treated one page as the whole documentation. The reasoning was actually
  sound — the skills docs page annotates twelve version floors and gives none for that field,
  so the absence looked like evidence. It was evidence *about that page*. Floors live in the
  release notes; hook output shapes live in the hooks reference. Three sources, different
  contents.
- **Fix:** `verified-facts.md` now opens with a table naming which source carries which kind
  of fact, and states the rule directly: check the release notes before recording an absence.
  A version-floor table sourced from the release notes replaces the "known unknown".
- **Codified:** not yet — first occurrence of *this* lesson. If a second confident absence
  turns out to be documented elsewhere, it becomes a rule: *an absence is a claim, and a
  claim needs its sources enumerated before it ships.*
