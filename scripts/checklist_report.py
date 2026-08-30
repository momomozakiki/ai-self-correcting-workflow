#!/usr/bin/env python3
"""Parse and reconcile worked-checklist reports against their golden files.

The shared parser behind `tests/test_checklist_reports.py` (shape, always run),
`scripts/checklist_status.py` (the closure gate) and
`scripts/checklist_growth.py` (evidence for `GROWTH.md`). One parser, so the gate
and the test cannot drift into disagreeing about what a valid report is.

Format contract: `golden-rules/REPORTING.md`.

A report mirrors its golden file's path::

    golden-rules/planning/risk-and-verification.md
      -> plans/<plan-stem>/checklists/planning/risk-and-verification.md

and carries a header, a **verdict block** of exactly the golden file's items in
order, and a free-form **Working notes** section that nothing counts.

The two-zone split is the whole safety property. An agent that can add lines to
the block deciding whether it is finished can always reach "finished" -- the
failure `docs/RETROSPECTIVE.md` records as *"a test that can be satisfied by
adjusting the data it measures is not a test"*. So the block is reconciled
against the golden file itself rather than against a stored snapshot: an added
line matches no item, a removed line leaves an item unaccounted for, and neither
check needs a baseline that could itself be edited.

Stdlib only, per `.claude/rules/repo-conventions.md`.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = REPO_ROOT / "golden-rules"
PLANS_ROOT = REPO_ROOT / "plans"

#: The five verdicts. `todo` is outstanding work: valid in flight, and the reason
#: `checklist_status.py` exists. See REPORTING.md for why an honest "I don't
#: know" (`cannot tell from here`) is first-class -- without it, a shape check
#: that demands an answer becomes a machine for manufacturing `pass`.
VERDICTS = ("pass", "finding", "cannot tell from here", "n/a", "todo")

#: Verdicts that must say why. `pass` needs no defence and `todo` has nothing to
#: say yet. Note the honest limit: this checks that a reason is *present*, never
#: that it is meaningful -- `n/a | ... | not applicable` satisfies it.
REASON_REQUIRED = ("finding", "cannot tell from here", "n/a")

NOTES_HEADING = "## Working notes"

CHECKBOX_RE = re.compile(r"^\s*- \[[ xX]\]\s*(.*)$")
VERDICT_LINE_RE = re.compile(r"^- (.*)$")
FENCE_RE = re.compile(r"^```")

#: Plans that are not task plans: transient hook state, the handover summary, and
#: anything already archived.
PLAN_EXEMPT = ("UNFINISHED.md", "HANDOVER.md")


def strip_fences(text):
    """Blank out fenced code blocks, keeping line numbering intact.

    `REPORTING.md` documents the format by showing a specimen report. Without
    this, the contract document trips every check it documents -- and the fix a
    reader reaches for is to weaken the check.
    """
    out, inside = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            inside = not inside
            out.append("")
            continue
        out.append("" if inside else line)
    return "\n".join(out)


def golden_items(path):
    """The checkbox items of a golden file, in order, as collapsed text.

    Continuation lines are folded in, so an item wrapped across three lines is
    one item. Only the count and order are load-bearing downstream; the text is
    carried so a generated skeleton is readable.
    """
    items, current = [], None
    for line in strip_fences(path.read_text(encoding="utf-8")).splitlines():
        match = CHECKBOX_RE.match(line)
        if match:
            if current is not None:
                items.append(" ".join(current.split()))
            current = match.group(1)
            continue
        if current is not None:
            if not line.strip() or line.startswith("#") or line.startswith("Sources"):
                items.append(" ".join(current.split()))
                current = None
            else:
                current += " " + line.strip()
    if current is not None:
        items.append(" ".join(current.split()))
    return items


def golden_status(path):
    """The golden file's `Status:` line, verbatim, or None."""
    for line in strip_fences(path.read_text(encoding="utf-8")).splitlines():
        if line.startswith("Status:"):
            return line.strip()
    return None


class Report:
    """A parsed report. Structure only -- validity is :func:`reconcile`'s job."""

    def __init__(self, path):
        self.path = path
        self.rel = path.relative_to(REPO_ROOT).as_posix()
        text = strip_fences(path.read_text(encoding="utf-8"))
        lines = text.splitlines()

        self.golden = self._field(lines, "Golden:")
        self.status = self._status_line(lines)
        self.worked = self._field(lines, "Worked:")

        # The zone boundary. Everything up to the notes heading is the verdict
        # block; everything after belongs to the agent and is never counted.
        try:
            split_at = lines.index(NOTES_HEADING)
            self.has_notes_heading = True
        except ValueError:
            split_at = len(lines)
            self.has_notes_heading = False
        self.notes = "\n".join(lines[split_at + 1:])

        self.verdicts = []
        for number, line in enumerate(lines[:split_at], start=1):
            match = VERDICT_LINE_RE.match(line)
            if not match:
                continue
            fields = [f.strip() for f in match.group(1).split("|")]
            self.verdicts.append({
                "line": number,
                "verdict": fields[0],
                "item": fields[1] if len(fields) > 1 else "",
                "reason": fields[2] if len(fields) > 2 else "",
            })

    @staticmethod
    def _field(lines, prefix):
        for line in lines:
            if line.startswith(prefix):
                return line[len(prefix):].strip()
        return None

    @staticmethod
    def _status_line(lines):
        for line in lines:
            if line.startswith("Status:"):
                return line.strip()
        return None

    def outstanding(self):
        """Verdict entries still marked `todo`."""
        return [v for v in self.verdicts if v["verdict"] == "todo"]


def golden_for(report_path):
    """The golden file a report's *path* implies, by mirroring.

    Derived from the path rather than read from the `Golden:` field, so the two
    can be cross-checked. A report that mirrors one file while citing another is
    a finding, not a detail.
    """
    parts = report_path.relative_to(PLANS_ROOT).parts
    if "checklists" not in parts:
        return None
    tail = parts[parts.index("checklists") + 1:]
    return GOLDEN_ROOT.joinpath(*tail)


def reconcile(report):
    """Every shape problem with ``report``. Empty list means well-formed."""
    problems = []
    golden = golden_for(report.path)

    if golden is None:
        return ["not under a plan's checklists/ directory"]
    if not golden.is_file():
        return ["no golden file at the mirrored path " + str(golden)]

    expected_rel = golden.relative_to(REPO_ROOT).as_posix()
    if report.golden is None:
        problems.append("no `Golden:` line")
    elif report.golden != expected_rel:
        problems.append("`Golden:` says {} but the path mirrors {}"
                        .format(report.golden, expected_rel))

    if report.worked is None:
        problems.append("no `Worked:` line")

    expected_status = golden_status(golden)
    if report.status is None:
        problems.append("no `Status:` line")
    elif expected_status is None:
        problems.append("the golden file carries no `Status:` line to match")
    elif report.status != expected_status:
        problems.append(
            "`Status:` does not match the golden file -- report has {!r}, "
            "golden now has {!r}. The checklist was edited after this report "
            "was worked; the answers are to a different version"
            .format(report.status, expected_status))

    if not report.has_notes_heading:
        problems.append("no `{}` heading -- the verdict block has no end, so "
                        "stray bullets below it would be counted as verdicts"
                        .format(NOTES_HEADING))

    items = golden_items(golden)
    if len(report.verdicts) != len(items):
        problems.append(
            "verdict block has {} lines, golden file has {} items. A line was "
            "added or removed -- the block must carry exactly the golden "
            "file's items, in order"
            .format(len(report.verdicts), len(items)))

    for entry in report.verdicts:
        where = "line {}".format(entry["line"])
        if entry["verdict"] not in VERDICTS:
            problems.append("{}: unknown verdict {!r} -- expected one of {}"
                            .format(where, entry["verdict"], ", ".join(VERDICTS)))
            continue
        if entry["verdict"] in REASON_REQUIRED and not entry["reason"]:
            problems.append("{}: `{}` needs a reason after a second `|`"
                            .format(where, entry["verdict"]))
    return problems


def plan_files():
    """Task plans: top-level `plans/*.md`, excluding transient and archived."""
    if not PLANS_ROOT.is_dir():
        return []
    return sorted(p for p in PLANS_ROOT.glob("*.md")
                  if p.name not in PLAN_EXEMPT)


def declared_checklists(plan_path):
    """The golden files a plan declares it owes reports for.

    Returns ``(paths, declared_none, raw)``. ``declared_none`` distinguishes a
    deliberate `none` from an absent line -- the difference between a recorded
    decision and an omission, which is the whole reason the line is mandatory.
    """
    raw = None
    for line in strip_fences(plan_path.read_text(encoding="utf-8")).splitlines():
        if line.startswith("Checklists:"):
            raw = line[len("Checklists:"):].strip()
            break
    if raw is None:
        return [], False, None
    if raw.lower().startswith("none"):
        return [], True, raw
    return [p.strip() for p in raw.split(",") if p.strip()], False, raw


def report_path_for(plan_path, checklist_rel):
    """Where a plan's report for ``checklist_rel`` must live."""
    return PLANS_ROOT / plan_path.stem / "checklists" / checklist_rel


def report_files():
    """Every report on disk, under any plan."""
    if not PLANS_ROOT.is_dir():
        return []
    return sorted(p for p in PLANS_ROOT.glob("*/checklists/**/*.md")
                  if p.is_file())


def skeleton(golden, plan_path, worked_on):
    """A fresh report for ``golden``, every verdict `todo`.

    This is what an agent writes *before* the work, so outstanding items are on
    disk from the start -- surviving both context loss and an interrupted
    session.
    """
    rel = golden.relative_to(GOLDEN_ROOT).as_posix()
    lines = [
        "# Checklist report — " + rel,
        "",
        "Golden: " + golden.relative_to(REPO_ROOT).as_posix(),
        golden_status(golden) or "Status: MISSING",
        "Worked: {} against {}".format(
            worked_on, plan_path.relative_to(REPO_ROOT).as_posix()),
        "",
    ]
    lines += ["- todo | " + item for item in golden_items(golden)]
    lines += ["", NOTES_HEADING, ""]
    return "\n".join(lines) + "\n"
