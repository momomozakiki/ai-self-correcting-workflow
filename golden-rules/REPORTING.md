# Reporting a worked checklist

Status: drafted by orchestrator 2026-08-31, unreviewed

`AUTHORING-GUIDE.md` is how to write a checklist. This is what you produce after working one.

Until 2026-08-31 the contract was prose — *"report the answers, including the ones that pass"* —
and **nothing anywhere checked that any answer was ever given**. A skipped item and a passed
item looked identical, because both looked like silence. This format exists to make that one
difference visible.

## The report is your to-do list, and you write it first

Generate the report **before** the work, from the golden file: one line per item, every verdict
`todo`. Then replace verdicts as you go.

Writing it up front is not bookkeeping. Two things it buys:

- **It survives context loss.** A checklist loaded at the start of a long task can fall out of
  context before the end, and nothing currently guarantees otherwise. A file does not.
- **It survives interruption.** A session that dies mid-task leaves its outstanding items named
  on disk, for the same reason `plans/UNFINISHED.md` exists.

## Where it lives

The report path mirrors the golden path, so the mapping is mechanical:

```
golden-rules/planning/risk-and-verification.md
  -> plans/<plan-stem>/checklists/planning/risk-and-verification.md
```

## The shape

```markdown
# Checklist report — planning/risk-and-verification.md

Golden: golden-rules/planning/risk-and-verification.md
Status: drafted by orchestrator 2026-08-30, unreviewed
Worked: 2026-08-31 against plans/golden-rules-migration.md

- pass | Does the plan touch anything irreversible
- finding | If this plan is abandoned halfway | stage 3 leaves .ai/ half-ported
- n/a | Is the rollback path stated | no shared or persistent state is touched
- todo | Is every count reproducible by a command

## Working notes

- The rollback item spawned three concrete steps; two done, one blocked on the archive path.
```

Fields are pipe-separated: `- <verdict> | <item text> | <reason>`. The item text is echoed so
the report reads on its own; nothing depends on its wording. The **reason** field is required
for `finding`, `cannot tell from here` and `n/a`, and optional for `pass` and `todo`.

`Status:` must be a **byte-identical copy** of the golden file's current stamp. That is what
makes ratification per-version rather than per-file: if the golden file is edited, the report
stops matching and you are told, instead of silently holding an answer to a question that has
since changed.

## The five verdicts

| Verdict | Means |
|---|---|
| `pass` | You checked, and it holds |
| `finding` | You checked, and it does not. The reason names what and where |
| `cannot tell from here` | You could not determine it. **A first-class answer** |
| `n/a` | The item's condition does not apply here. The reason says why |
| `todo` | Not yet worked. Valid in flight; fails the closure gate |

`cannot tell from here` exists for the same reason `stage-gate-auditor` has **cannot verify**:
*"An auditor that never returns cannot verify is guessing and calling it certainty."* Without an
honest "I don't know", a shape check that demands an answer becomes a machine for manufacturing
`pass`.

## Two zones, and the split is the whole point

**The verdict block** — between the header and `## Working notes` — carries exactly the golden
file's items, in order, one line each. You may change a verdict. You may **not** add or remove a
line.

**Working notes** — everything after that heading — is yours. Decomposition, discovered steps,
anything. It grows freely and **nothing counts it**.

Merging them is the one change that breaks this format. An agent that can add items to the thing
deciding whether it is finished can always reach "finished" — the failure `RETROSPECTIVE.md`
records as *"a test that can be satisfied by adjusting the data it measures is not a test"*, and
the same defect that retired the maturity tracker.

**A discovered step is not discarded.** Record it in Working notes during the task. A step that
recurs — the two-occurrence threshold in `GROWTH.md`, same as everything else — gets **promoted
into the golden file**, where it becomes a counted item for every future task. The list grows at
two speeds: freely within a task, changing nothing about completion; and on evidence across
tasks, growing the measuring stick itself.

## The reports are the evidence base for improving the checklist

This is the second reason to keep them, and over time probably the larger one. `GROWTH.md` has
always said an item that never applies is a strike candidate — but until now that was somebody's
impression. A corpus of reports makes it **countable**, and each of GROWTH's criteria has a
signal in the data:

| Signal across reports | What it is evidence of |
|---|---|
| An item repeatedly `cannot tell from here` | **Unanswerable** — a strike criterion. Nobody can tell whether it passed, so it has been ticked without being checked |
| An item repeatedly `n/a` | Its condition never fires. Either the group's *when* is wrong, or the item belongs in a narrower file |
| The same step recurring in Working notes | **Depth growth** — the golden file is missing an item. Promote it |
| Two items that always share a verdict | Possible **duplication** — a strike criterion. Two items, one decision |
| An item that always **passes** | **Nothing.** Not a strike. A rule that prevents failures produces no failures |

`scripts/checklist_growth.py` tallies these and prints candidates. Three things it deliberately
does not do:

- **It never strikes anything.** It prints candidates for a human to rule on, because that is
  what `GROWTH.md` already requires: *"Drift is reported for human ratification instead."* An
  agent that both applies a rule and decides its fate is the loop this repository killed.
- **It sets no threshold.** A number to clear is a number to game, and the repository has
  already recorded an item's data being nudged to satisfy a validator.
- **It prints the reason strings, not just the tallies.** `n/a` is the cheapest verdict to
  write, so a pile of them may mean the item is wrong *or* that someone was avoiding work — and
  those look identical in a count. Only the reasons distinguish them.

## Declaring what is owed

Every plan carries one `Checklists:` line naming the golden files it owes reports for:

```
Checklists: planning/risk-and-verification.md, security/review.md
```

Declaring nothing is a decision, not an omission, and is written as one:

```
Checklists: none — single-line wording fix, no domain applies
```

Below roughly `small_change`, `none` is the expected answer. A twenty-item verdict sheet for a
one-line change is cost with no return, on top of the token-budget regression `README.md`
already admits.

## What checks this, and what it cannot

`tests/test_checklist_reports.py` runs always and checks **shape**: the verdict vocabulary, one
line per golden item in order, the two-zone boundary, required reasons, the `Status:` match, and
that every declared checklist has a report.

`scripts/checklist_status.py` is the **closure gate** and is deliberately *not* a unit test. It
lists outstanding `todo`s and exits non-zero when any remain. Run it at Phase 3, beside the
ledger and archive steps.

They are separate on purpose. Folding "everything answered" into the suite would leave it red
for the whole duration of every task — which destroys the meaning of a red suite, and worse,
creates pressure to fill verdicts early to get back to green. That is *mark-then-do*: precisely
the fabrication neither check can detect.

### What none of it catches — read this before relying on it

- **Fabrication.** Write `pass` on every line without looking and everything goes green. This
  format makes *omission* impossible and does nothing about *dishonesty*.
- **Avoidance.** The whole chain rests on a `Checklists:` line you write yourself.
  `Checklists: none — trivial` passes. So this catches **sloppiness** — a checklist started and
  not finished — and not **avoidance** — one never declared.
- **Under-declaration.** Declaring `git` for a task that also touched authentication passes.
- **A reason that says nothing.** `n/a | ... | not applicable` satisfies the requirement. The
  check is on shape, not substance.
- **An edited golden base.** The verdict block is validated against the golden file, so editing
  the golden file makes both consistent. Ratified golden files are due to become Tier-0
  protected paths; until they are, this format inherits that hole and cannot close it.

The mitigations for the first two are a human reading the report and the declaration sitting in
the plan at Phase 1, where objecting is still cheap. Both are readers, not mechanisms, and are
recorded as such rather than dressed up.
