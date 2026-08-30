# Authoring a golden rule

Status: drafted by orchestrator 2026-08-30, unreviewed

Every domain added to this library inherits the quality of this file. `README.md` says what the
format *is*; this says how to write something worth putting in it.

The one-line test: **a golden rule exists because of a failure it prevents.** If you cannot name
the failure, you are writing a preference.

This file is read, not ticked. Its bullets are plain `-`, not `- [ ]`, deliberately: it is not
a domain checklist an agent loads per task, so it is not bound by the ~20-item ceiling it sets
below, and it should not be counted as though it were.

## What earns a place

- Name the failure. Not "bad things could happen" — a specific wrong outcome someone
  reached, or a specific one this item makes unreachable. If the honest answer is "none
  yet", the item belongs in a project layer (`plans/<project>/checklists/<domain>.md`)
  until it has one.
- Apply the portability test: **is it still right in another language, on another team, in
  a repo you have never seen?** A golden rule is carried into every project unchanged. One
  that assumes this repo's directory names, tooling or team habits will be wrong somewhere
  and read as noise everywhere else.
- Project-specific names — a service, a branch convention, a CI job — belong in the project
  layer. The base can say *"check what `git add -A` would sweep in"*; only the project layer
  can say *"`plans/UNFINISHED.md` is rewritten every turn"*.
- Prefer few items that fire to many that might. A file nobody finishes reading protects
  nothing.

Sources: `GROWTH.md`, the "seeded empty" principle — *a rule nobody hit yet is a guess; a rule
harvested from a real mistake is knowledge*. Held here since 2026-08-05. Note the honest limit:
this repository has **not** measured which of its items ever caught anything, so the principle
is a design commitment, not a finding.

## Altitude — the mistake to worry about most

This is where checklists go wrong, and it goes wrong quietly: a wrong-altitude item still reads
well.

- Where there is **one correct action**, write the **command**. `git pull --rebase`, not
  "consider whether to rebase". Git, deployment, release mechanics: mostly this kind.
- Where the answer **depends on the code in front of you**, write a **question**. *"Does
  this name say what it is for?"*, not "use descriptive names". Architecture, code quality,
  API design: mostly this kind.
- Test which kind you have by asking whether you could write the right answer down **now,
  without seeing the codebase**. If yes, it is a command. If no, any prescription you write
  is a guess about a repository you have not read.
- A prescription at the wrong altitude stops being right the moment the codebase differs
  from the one it was written for — and it goes on being followed anyway, because it looks
  like an instruction. That is how the previous library got brittle.
- A question at the wrong altitude has the opposite failure: *"is the deployment safe?"*
  makes the reader re-derive an answer that was already known. If you know it, say it.

Sources: reasoned from first principles, 2026-08-30, codifying the checklist-not-prescription
rule this repository has applied since 2026-08-05 and the altitude finding from the design
review of `plans/golden-rules-migration.md`.

## Writing the item

- **Checkable.** Two readers take the same action from it, and afterwards you can tell
  whether it was done. "Review error handling" fails both halves.
- **One decision per item.** An "and" is usually two items. A compound item cannot be
  half-passed, so it gets ticked when the easier half is done.
- **Give the *why* inline**, in the same breath — usually after an em dash. An item whose
  reason lives somewhere else gets followed mechanically until it is inconvenient, then
  dropped. Where the why is an incident, the `Sources:` line carries it instead.
- **Do not restate what a tool already enforces.** If the formatter, the type checker or a
  hook already fails the build, the item costs attention and buys nothing. Being
  already-tool-enforced is grounds for striking an existing item (`GROWTH.md`).
- Write it so failing is *observable*. If nothing would look different when the item is
  ignored, you have written an aspiration.

Sources: reasoned from first principles, 2026-08-30; the "checkable / one decision / why
inline" triple is the working form this repository's own checklists converged on.

## Shape of the file

- **Group by *when it applies*, not by topic.** "Before pushing" is a group; "Branching" is
  a topic. Grouping by when is what lets a reader skip five groups honestly instead of
  skimming all of them.
- Give each group a `##` heading and exactly one `Sources:` line, at the end of the group.
- **~20 checkbox items is the ceiling for a file.** Past that, split — by phase
  (`new-project.md` / `existing-project.md`) or by variant — rather than growing one file.
- Splitting is not a defeat. The file is the unit an agent loads, so file size *is* the
  token budget: a split is how a task pulls in the half that applies to it.
- Cross-link the halves in the `Applies when` line, so a reader who opened the wrong one
  finds the right one immediately.
- **When you merge two groups, check whether you wrote "and" where "or" was meant.** Merging
  is how a conversion keeps the file under the ceiling, and it is where conditions quietly
  narrow: two groups that each applied on their own condition become one that applies only
  when *both* hold, and the items that used to fire for one case alone stop firing. This is
  recorded here rather than as a checklist item because it has happened once, which is below
  the promotion threshold in `GROWTH.md` — but it happened during the conversion this guide
  was written for, and it cost two items their coverage until a second reader recounted.

Sources: reasoned from first principles, 2026-08-30. The ceiling is enforced by
`tests/test_golden_rules.py`; the number is a judgement, the enforcement is not.

## Sourcing — where the item came from

- One `Sources:` line per `##` group. Not per item: per group. If two items in a group need
  different authorities, they are probably two groups.
- An authority citation is **version-pinned**: `Pro Git, 2nd ed. (2014)`, not `Pro Git`.
  `OWASP ASVS 5.0.0`, not `OWASP ASVS`. For a moving document, pin the retrieval date and
  the version you read: `code.claude.com/docs/en/skills, retrieved 2026-08-06 (Claude Code
  v2.1.221)`.
- An **incident** citation is dated and names what happened:
  `Incident 2026-08-29 — branched from a base missing every file the plan targeted.` This
  is not a weaker citation than an authority. It is usually stronger: it is the only kind
  guaranteed to have prevented something real.
- Where there is neither, write the honest fallback: `Source: reasoned from first
  principles, YYYY-MM-DD`. This is a legitimate, complete answer. It flags the group for
  review, which a fabricated citation does not.
- **Never cite what you have not read.** A plausible-looking standard number is worse than
  no citation, because it survives review by looking finished.
- **The test will not save you here.** `tests/test_golden_rules.py` catches the *absence* of a
  version, never a *wrong* one. `RFC 7231 (2014)` — obsoleted by 9110 — passes. `IEEE
  1012-2016`, `OWASP ASVS 4.0.3`, `ISO 31000:2009` and `OWASP ASVS 5.0.0 Level 9` all pass.
  Those are the five defect classes the old library's `source_version` field is credited with
  catching, and **the pin check catches none of them**. Currency is yours to check, and the
  honest move when you have not is to say so in the line, as
  `golden-rules/security/review.md` does.

Sources: `plans/golden-rules-migration.md` (stage 2 measurement, 2026-08-30, reproduced by
script). In the JSON library this replaces, the mandatory `source_version` field was a
byte-identical copy of `source` in **104 of 119 items**, and **50 of 119 carried no version
token at all** — no year, no edition, no number: "The Pragmatic Programmer, Hunt & Thomas",
"Google SRE Book", "The Twelve-Factor App". Whole domains were duplicated 8/8, 10/10, 12/12.
The two numbers differ because a duplicated string can still be a pin: "OWASP ASVS 5.0.0"
appears in both fields and is perfectly good. **A required field is not a pin.** The one file
that did it properly (`rule-skill-authoring-review.json`, 0/8 duplicated) did it because
someone chose to, which is why this guidance lives here and not only in a schema.

## Anti-patterns — recognisable on sight

- **Aspirational.** "Strive for clean interfaces." Nothing to do, nothing to check.
- **Unfalsifiable.** "Consider performance." Consideration cannot be observed; the item
  passes whatever you did.
- **Copied from a framework's documentation.** It ages with that framework, not with you,
  and it usually encodes that framework's defaults as universal truths.
- **A file that only ever grows.** Additions are visible and easy; strikes are invisible
  and nobody does them. If a file has never lost an item, it has not been maintained — see
  the strike criteria in `GROWTH.md`, and note that **passing is never one of them**.
- **The rule that documents the tool.** If the answer is in `--help`, link the tool.
- **The rule written for the last incident only.** Ask what class the incident belongs to;
  write the class, mention the incident in `Sources:`.

Sources: reasoned from first principles, 2026-08-30. The "only ever grows" entry is stated as a
risk, not as a measured finding: the library this replaces reached 119 items, and the only
rule-file deletions in its history (`rule-clean-code-review.json`, `rule-solid-review.json` at
`ceb17c2`) were a consolidation, not a strike on the evidence.

## Before you call it ratified

- **Run it against real work** — a real repository for a domain file, a real plan for a
  planning file. A checklist that finds nothing in a thousand lines is too vague to be
  worth loading, and reading it will not tell you that.
- Trial it against something **you** wrote, not something convenient. A checklist that
  flatters the work it shipped with has not been tested.
- Record what the trial found, **including which items did not apply**. Items that never
  apply anywhere are the next strike candidates.
- Stamp it. `Status: ratified YYYY-MM-DD` means a human read this version. If you are an
  agent filling a gap, the stamp is `Status: drafted by orchestrator YYYY-MM-DD,
  unreviewed`, and you say so in your report.

Sources: `GROWTH.md` (trial-before-keeping); `plans/golden-rules-migration.md` gate 6, which
requires exactly this reading before an authored file is trusted.
