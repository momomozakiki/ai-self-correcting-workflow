#!/usr/bin/env python3
"""Diff the *collected test IDs* of this worktree against a pinned baseline commit.

Gate 1 of ``plans/golden-rules-migration.md`` asks whether the stage removed any
test coverage that was not authorised. A raw test *count* cannot answer that: it
cannot tell twenty tests deleted alongside the feature they tested from twenty
tests that silently stopped being collected. The set of collected IDs can.

The criterion was amended from a count floor to this diff by the agent whose own
work failed the count -- a conflict of interest recorded in the plan. The
objection that stood was not that the diff is weaker, but that a *hand-read* list
of removals is exactly as fallible as the count it replaced: the paragraph
arguing for it was wrong twice about its own arithmetic. This script exists so
that the diff is taken mechanically instead of read. Run it; do not retype it.

Usage::

    python scripts/test_id_diff.py                     # against the pinned baseline
    python scripts/test_id_diff.py --baseline <rev>    # against some other commit

Output is the removed and added IDs, sorted, with counts. Exit status is 0 when
both trees were collected successfully -- including when IDs were removed. This
script reports; it does not judge. Deciding whether each removal has a recorded
reason at the site it was removed from is the gate's job, not the tool's.

Stdlib only, per ``.claude/rules/repo-conventions.md``.

Implementation notes, both learned the hard way:

* The two trees are collected in **separate subprocesses**. ``unittest``
  discovery imports the test modules by bare name (``test_hook``), so collecting
  two trees in one process would hand the second tree the first tree's already
  imported modules out of ``sys.modules``.
* Discovery passes ``start_dir='tests'`` and **no** ``top_level_dir``. ``tests/``
  has no ``__init__.py``, so naming it as the top level raises ``ImportError``
  before anything is collected.
"""

import argparse
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The stage-0 baseline: the last commit before Stage 1 touched the suite.
#: Pinned, because an ID diff against a floating baseline is unfalsifiable --
#: "nothing was removed since whatever I happened to compare against" is not a
#: claim anyone can check twice and get the same answer.
DEFAULT_BASELINE = "4353d8b"


def collect_ids(tree):
    """Every test ID ``unittest`` collects under ``<tree>/tests``.

    Returns a sorted list. Discovery errors surface as
    ``unittest.loader._FailedTest`` IDs rather than exceptions, so they are
    returned like any other ID and reported by the caller -- a tree that fails
    to import is a finding, not a crash.
    """
    suite = unittest.defaultTestLoader.discover(start_dir="tests")
    ids = []

    def walk(node):
        if isinstance(node, unittest.TestSuite):
            for child in node:
                walk(child)
        else:
            ids.append(node.id())

    walk(suite)
    return sorted(ids)


def collect_in_subprocess(tree):
    """Run :func:`collect_ids` against ``tree`` in a fresh interpreter."""
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--collect"],
        cwd=str(tree),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(
            "collection failed in {}\n--- stdout ---\n{}\n--- stderr ---\n{}".format(
                tree, result.stdout, result.stderr
            )
        )
    return [line for line in result.stdout.splitlines() if line.strip()]


def export_baseline(rev, destination):
    """Extract ``rev`` into ``destination`` via ``git archive``.

    The tarball is written to a file and unpacked with :mod:`tarfile` rather than
    piped into ``tar``, so this does not depend on a ``tar`` binary being on
    PATH and does not need a shell pipeline.
    """
    archive = destination / "baseline.tar"
    subprocess.run(
        ["git", "-C", str(REPO_ROOT), "archive", "--format=tar",
         "--output=" + str(archive), rev],
        check=True,
    )
    tree = destination / "tree"
    tree.mkdir()
    with tarfile.open(archive) as tar:
        tar.extractall(tree)
    return tree


def describe(rev):
    """One-line description of ``rev``, for the report header."""
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "log", "--oneline", "-1", rev],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--baseline", default=DEFAULT_BASELINE,
                        help="commit to compare against (default: %(default)s)")
    parser.add_argument("--collect", action="store_true",
                        help=argparse.SUPPRESS)  # internal: used per subprocess
    args = parser.parse_args(argv)

    if args.collect:
        for test_id in collect_ids(Path.cwd()):
            print(test_id)
        return 0

    with tempfile.TemporaryDirectory() as scratch:
        baseline_tree = export_baseline(args.baseline, Path(scratch))
        before = collect_in_subprocess(baseline_tree)
        after = collect_in_subprocess(REPO_ROOT)

    removed = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))

    print("baseline {}: {}".format(args.baseline, describe(args.baseline)))
    print("baseline collected : {}".format(len(before)))
    print("worktree collected : {}".format(len(after)))
    print("removed: {}   added: {}".format(len(removed), len(added)))

    print("\nREMOVED ({})".format(len(removed)))
    for test_id in removed:
        print("  - " + test_id)
    print("\nADDED ({})".format(len(added)))
    for test_id in added:
        print("  + " + test_id)

    failed = [t for t in before + after if "_FailedTest" in t]
    if failed:
        print("\nWARNING: discovery errors present; the diff above is unreliable:")
        for test_id in sorted(set(failed)):
            print("  ! " + test_id)

    print("\nEach removed ID needs a recorded reason at the site it was removed "
          "from. This script does not check that.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
