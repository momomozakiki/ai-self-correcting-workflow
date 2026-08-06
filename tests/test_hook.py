#!/usr/bin/env python3
"""Synthetic-event tests for the workflow hook dispatcher.

Stdlib ``unittest`` only -- run with::

    python -m unittest discover -s tests
    # or
    python -m unittest tests.test_hook

Each test drives ``workflow_hook.main`` with a fabricated hook event on stdin
and asserts on the JSON emitted to stdout, mirroring how Claude Code invokes
the hook. State is isolated per-test via a unique ``session_id`` and a temp
``CLAUDE_PROJECT_DIR``.
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from contextlib import redirect_stdout
from pathlib import Path

# Make the sibling hooks/ package importable regardless of CWD.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "hooks"))

import workflow_hook  # noqa: E402


def run_hook(event, argv=None, project_dir=None):
    """Invoke the dispatcher with ``event`` on stdin; return parsed stdout (or None)."""
    stdin = io.StringIO(json.dumps(event))
    buf = io.StringIO()
    old_stdin, sys.stdin = sys.stdin, stdin
    old_env = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir is not None:
        os.environ["CLAUDE_PROJECT_DIR"] = str(project_dir)
    try:
        with redirect_stdout(buf):
            rc = workflow_hook.main(argv or [])
    finally:
        sys.stdin = old_stdin
        if old_env is None:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
        else:
            os.environ["CLAUDE_PROJECT_DIR"] = old_env
    out = buf.getvalue().strip()
    parsed = json.loads(out) if out else None
    return rc, parsed


class BaseCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        (self.project / ".claude").mkdir()
        (self.project / "src").mkdir()
        (self.project / "docs").mkdir()
        (self.project / "history").mkdir()
        self.session_id = f"test-{uuid.uuid4()}"
        self.write_config({
            "project_root": ".",
            "roadmap_file": "ROADMAP.md",
            "ledger": {"enabled": True, "directory": "history"},
            "source_directories": ["src"],
            "documentation_directories": ["docs"],
            "env_check": {"tool_paths": {}},
            "stop_hook": {"max_blocks": 2, "main_branch": "main"},
        })

    def tearDown(self):
        try:
            workflow_hook.state_path(self.session_id).unlink()
        except OSError:
            pass
        self.tmp.cleanup()

    def write_config(self, cfg):
        (self.project / ".claude" / "workflow_config.json").write_text(
            json.dumps(cfg), encoding="utf-8")

    def edit_event(self, file_path):
        return {"hookEventName": "PostToolUse", "session_id": self.session_id,
                "tool_name": "Edit", "tool_input": {"file_path": file_path}}


class TestFailSoft(BaseCase):
    def test_unparseable_stdin_exits_zero(self):
        sys.stdin = io.StringIO("not json {{{")
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = workflow_hook.main([])
        finally:
            sys.stdin = sys.__stdin__
        self.assertEqual(rc, 0)
        self.assertEqual(buf.getvalue().strip(), "")

    def test_unknown_event_no_output(self):
        rc, out = run_hook({"hookEventName": "Nonsense"}, project_dir=self.project)
        self.assertEqual(rc, 0)
        self.assertIsNone(out)

    def test_missing_session_id_still_runs(self):
        rc, out = run_hook({"hookEventName": "SessionStart"}, project_dir=self.project)
        self.assertEqual(rc, 0)
        self.assertIn("hookSpecificOutput", out)


class TestSessionStart(BaseCase):
    def test_emits_context(self):
        rc, out = run_hook(
            {"hookEventName": "SessionStart", "session_id": self.session_id},
            project_dir=self.project)
        self.assertEqual(rc, 0)
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("session start", out["hookSpecificOutput"]["additionalContext"].lower())

    def test_reload_skills_when_a_skills_directory_exists(self):
        """Live change detection does not watch a skills directory created after
        the session started -- which is how this repository once ran for months
        with skills that were never loaded. Asking for a re-scan removes it."""
        (self.project / ".claude" / "skills" / "demo").mkdir(parents=True)
        rc, out = run_hook(
            {"hookEventName": "SessionStart", "session_id": self.session_id},
            project_dir=self.project)
        self.assertIs(True, out["hookSpecificOutput"].get("reloadSkills"))

    def test_no_reload_skills_without_a_skills_directory(self):
        """The flag should mean something when it appears; a project with no
        skills would be asking for a scan that can only find nothing."""
        rc, out = run_hook(
            {"hookEventName": "SessionStart", "session_id": self.session_id},
            project_dir=self.project)
        self.assertNotIn("reloadSkills", out["hookSpecificOutput"])

    def test_env_check_null_version_flag_existence(self):
        # A tool with version_flag=null: only existence is checked.
        tool = self.project / "mytool.bin"
        tool.write_text("x", encoding="utf-8")
        self.write_config({
            "project_root": ".",
            "source_directories": ["src"],
            "documentation_directories": ["docs"],
            "ledger": {"directory": "history"},
            "env_check": {"tool_paths": {
                "mytool": {"path": str(tool), "version_flag": None}}},
        })
        rc, out = run_hook(
            {"hookEventName": "SessionStart", "session_id": self.session_id},
            project_dir=self.project)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("mytool: found", ctx)

    def test_env_check_missing_tool_reports_not_found(self):
        self.write_config({
            "project_root": ".",
            "source_directories": ["src"],
            "documentation_directories": ["docs"],
            "ledger": {"directory": "history"},
            "env_check": {"tool_paths": {
                "ghost": {"path": "/no/such/tool", "version_flag": None}}},
        })
        rc, out = run_hook(
            {"hookEventName": "SessionStart", "session_id": self.session_id},
            project_dir=self.project)
        self.assertIn("ghost: NOT FOUND",
                      out["hookSpecificOutput"]["additionalContext"])

    def test_roadmap_next_action_parsed(self):
        (self.project / "ROADMAP.md").write_text(
            "# Roadmap\n\n**Next action:** wire up the Stop hook\n", encoding="utf-8")
        rc, out = run_hook(
            {"hookEventName": "SessionStart", "session_id": self.session_id},
            project_dir=self.project)
        self.assertIn("wire up the Stop hook",
                      out["hookSpecificOutput"]["additionalContext"])

    def test_roadmap_ignores_inline_mention(self):
        # A prose line that merely mentions the marker inside backticks must not
        # be matched; only the real leading-marker line counts.
        (self.project / "ROADMAP.md").write_text(
            "# Roadmap\n\nThe hook parses the first `**Next action:**` line below.\n\n"
            "**Next action:** the real task\n", encoding="utf-8")
        rc, out = run_hook(
            {"hookEventName": "SessionStart", "session_id": self.session_id},
            project_dir=self.project)
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("the real task", ctx)
        self.assertNotIn("line below", ctx)


class TestPostToolUse(BaseCase):
    def test_source_edit_sets_flag_no_output_when_doc_also_touched(self):
        # MultiEdit touching a source AND a doc file -> no nudge.
        event = {"hookEventName": "PostToolUse", "session_id": self.session_id,
                 "tool_name": "MultiEdit",
                 "tool_input": {"file_path": "src/a.py",
                                "edits": [{"file_path": "docs/b.md"}]}}
        rc, out = run_hook(event, project_dir=self.project)
        self.assertIsNone(out)  # doc touched this call -> suppress nudge
        state = workflow_hook.load_state(self.session_id)
        self.assertTrue(state["source_changed"])

    def test_source_edit_emits_nudge_once(self):
        rc, out = run_hook(self.edit_event("src/a.py"), project_dir=self.project)
        self.assertIsNotNone(out)
        self.assertIn("ledger", out["hookSpecificOutput"]["additionalContext"].lower())
        # Second source edit -> no repeat nudge.
        rc, out2 = run_hook(self.edit_event("src/c.py"), project_dir=self.project)
        self.assertIsNone(out2)

    def test_ledger_edit_sets_ledger_touched(self):
        run_hook(self.edit_event("history/2026-W28.md"), project_dir=self.project)
        state = workflow_hook.load_state(self.session_id)
        self.assertTrue(state["ledger_touched"])
        self.assertFalse(state["source_changed"])

    def test_non_source_edit_no_flag(self):
        run_hook(self.edit_event("README.md"), project_dir=self.project)
        state = workflow_hook.load_state(self.session_id)
        self.assertFalse(state["source_changed"])

    def test_skill_edit_nudges_once(self):
        """Skills fail silently in every direction, so the moment just after one
        is written is the only cheap place to say so."""
        rc, out = run_hook(self.edit_event(".claude/skills/demo/SKILL.md"),
                           project_dir=self.project)
        self.assertIsNotNone(out, "editing a skill emitted no advisory")
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("skill-authoring", ctx)
        self.assertIn("templates/skills", ctx)
        self.assertTrue(workflow_hook.load_state(self.session_id)["skill_nudged"])

        # Advisory, not a gate: it must not repeat, and must never block.
        self.assertNotIn("decision", out)
        rc, again = run_hook(self.edit_event(".claude/skills/other/SKILL.md"),
                             project_dir=self.project)
        self.assertIsNone(again, "the skill advisory repeated")

    def test_editing_a_reference_under_a_skill_also_nudges(self):
        rc, out = run_hook(
            self.edit_event(".claude/skills/demo/references/notes.md"),
            project_dir=self.project)
        self.assertIsNotNone(out)
        self.assertIn("skill-authoring",
                      out["hookSpecificOutput"]["additionalContext"])

    def test_a_non_skill_edit_does_not_nudge_about_skills(self):
        rc, out = run_hook(self.edit_event("README.md"), project_dir=self.project)
        self.assertIsNone(out)
        self.assertFalse(workflow_hook.load_state(self.session_id)["skill_nudged"])


class TestStop(BaseCase):
    def _seed_state(self, **kw):
        state = workflow_hook.default_state()
        state.update(kw)
        workflow_hook.save_state(self.session_id, state)

    def test_ledger_reminder_when_source_changed_unlogged(self):
        self._seed_state(source_changed=True, ledger_touched=False)
        rc, out = run_hook(
            {"hookEventName": "Stop", "session_id": self.session_id},
            project_dir=self.project)
        self.assertEqual(out["decision"], "block")
        self.assertIn("ledger", out["reason"].lower())
        # block count incremented
        self.assertEqual(
            workflow_hook.load_state(self.session_id)["stop_block_count"], 1)

    def test_no_block_when_ledger_touched(self):
        self._seed_state(source_changed=True, ledger_touched=True)
        rc, out = run_hook(
            {"hookEventName": "Stop", "session_id": self.session_id},
            project_dir=self.project)
        self.assertIsNone(out)

    def test_stop_hook_active_short_circuits(self):
        self._seed_state(source_changed=True, ledger_touched=False)
        rc, out = run_hook(
            {"hookEventName": "Stop", "session_id": self.session_id,
             "stop_hook_active": True},
            project_dir=self.project)
        self.assertIsNone(out)

    def test_max_blocks_cap(self):
        self._seed_state(source_changed=True, ledger_touched=False, stop_block_count=2)
        rc, out = run_hook(
            {"hookEventName": "Stop", "session_id": self.session_id},
            project_dir=self.project)
        self.assertIsNone(out)  # already at cap -> allow stop


class TestStopBreadcrumb(BaseCase):
    """Workstream A: the Phase-3 auto-breadcrumb on a dirty tree."""

    def _seed_state(self, **kw):
        state = workflow_hook.default_state()
        state.update(kw)
        workflow_hook.save_state(self.session_id, state)

    def _run_stop_with_status(self, status):
        """Drive a Stop event with git_status/_git stubbed to `status`."""
        orig_git_status = workflow_hook.git_status
        orig_git = workflow_hook._git
        workflow_hook.git_status = lambda project_root: status
        # _git is used inside the breadcrumb for `status --porcelain`.
        workflow_hook._git = lambda root, *args: (
            " M src/a.py\n?? new.txt" if args[:1] == ("status",) else None)
        try:
            return run_hook(
                {"hookEventName": "Stop", "session_id": self.session_id},
                project_dir=self.project)
        finally:
            workflow_hook.git_status = orig_git_status
            workflow_hook._git = orig_git

    def test_dirty_tree_writes_breadcrumb_on_feature_branch(self):
        self._seed_state()
        self._run_stop_with_status(
            {"branch": "feat/x", "dirty": True, "ahead": None, "behind": None})
        bc = self.project / "plans" / "UNFINISHED.md"
        self.assertTrue(bc.is_file())
        text = bc.read_text(encoding="utf-8")
        self.assertIn(workflow_hook.BREADCRUMB_MARKER, text)
        self.assertIn("feat/x", text)
        self.assertIn("src/a.py", text)  # porcelain file list included

    def test_dirty_tree_writes_breadcrumb_on_main(self):
        self._seed_state()
        self._run_stop_with_status(
            {"branch": "main", "dirty": True, "ahead": None, "behind": None})
        self.assertTrue((self.project / "plans" / "UNFINISHED.md").is_file())

    def test_clean_tree_writes_no_breadcrumb(self):
        self._seed_state()
        self._run_stop_with_status(
            {"branch": "feat/x", "dirty": False, "ahead": None, "behind": None})
        self.assertFalse((self.project / "plans" / "UNFINISHED.md").exists())

    def test_human_unfinished_is_not_overwritten(self):
        self._seed_state()
        plans = self.project / "plans"
        plans.mkdir()
        human = plans / "UNFINISHED.md"
        human.write_text("# My real handoff plan\nstep 1\n", encoding="utf-8")
        self._run_stop_with_status(
            {"branch": "feat/x", "dirty": True, "ahead": None, "behind": None})
        self.assertEqual(human.read_text(encoding="utf-8"),
                         "# My real handoff plan\nstep 1\n")

    def test_own_breadcrumb_is_overwritten_idempotently(self):
        self._seed_state()
        plans = self.project / "plans"
        plans.mkdir()
        bc = plans / "UNFINISHED.md"
        bc.write_text(workflow_hook.BREADCRUMB_MARKER + "\nold content\n",
                      encoding="utf-8")
        self._run_stop_with_status(
            {"branch": "feat/x", "dirty": True, "ahead": None, "behind": None})
        text = bc.read_text(encoding="utf-8")
        self.assertIn(workflow_hook.BREADCRUMB_MARKER, text)
        self.assertNotIn("old content", text)  # refreshed, not appended


class TestF5UpdateCheck(BaseCase):
    """Workstream B: opt-in daily workflow-core update check."""

    def _cfg(self, **overrides):
        base = {
            "project_root": ".",
            "source_directories": ["src"],
            "documentation_directories": ["docs"],
            "ledger": {"directory": "history"},
            "env_check": {"tool_paths": {}},
        }
        if overrides:
            base["workflow_update_check"] = overrides
        return base

    def test_disabled_is_noop_and_makes_no_git_calls(self):
        calls = []
        orig = workflow_hook._git
        workflow_hook._git = lambda root, *a: calls.append(a) or None
        try:
            notice = workflow_hook.check_workflow_updates(
                self._cfg(enabled=False), self.project)
        finally:
            workflow_hook._git = orig
        self.assertIsNone(notice)
        self.assertEqual(calls, [])

    def test_missing_submodule_is_noop(self):
        notice = workflow_hook.check_workflow_updates(
            self._cfg(enabled=True), self.project)
        self.assertIsNone(notice)

    def test_same_day_check_is_skipped(self):
        # Link a fake submodule so we pass the .git existence gate.
        sub = self.project / ".claude" / "workflow-core"
        sub.mkdir(parents=True)
        (sub / ".git").write_text("gitdir: x", encoding="utf-8")
        ai = self.project / ".ai"
        ai.mkdir()
        import time as _t
        (ai / ".workflow_check_date").write_text(
            _t.strftime("%Y-%m-%d"), encoding="utf-8")
        called = []
        orig = workflow_hook._git
        workflow_hook._git = lambda root, *a: called.append(a) or None
        try:
            notice = workflow_hook.check_workflow_updates(
                self._cfg(enabled=True), self.project)
        finally:
            workflow_hook._git = orig
        self.assertIsNone(notice)
        self.assertEqual(called, [])  # date-gated: no fetch today

    def test_behind_submodule_emits_notice_and_writes_date(self):
        sub = self.project / ".claude" / "workflow-core"
        sub.mkdir(parents=True)
        (sub / ".git").write_text("gitdir: x", encoding="utf-8")

        def fake_git(root, *args):
            if args[:1] == ("fetch",):
                return ""
            if args[:1] == ("rev-list",):
                return "3"
            return None
        orig = workflow_hook._git
        workflow_hook._git = fake_git
        try:
            notice = workflow_hook.check_workflow_updates(
                self._cfg(enabled=True), self.project)
        finally:
            workflow_hook._git = orig
        self.assertIsNotNone(notice)
        self.assertIn("3 new commits", notice)
        import time as _t
        self.assertEqual(
            (self.project / ".ai" / ".workflow_check_date").read_text(
                encoding="utf-8").strip(), _t.strftime("%Y-%m-%d"))

    def test_up_to_date_submodule_is_silent(self):
        sub = self.project / ".claude" / "workflow-core"
        sub.mkdir(parents=True)
        (sub / ".git").write_text("gitdir: x", encoding="utf-8")
        workflow_hook_git = lambda root, *a: "" if a[:1] == ("fetch",) else (
            "0" if a[:1] == ("rev-list",) else None)
        orig = workflow_hook._git
        workflow_hook._git = workflow_hook_git
        try:
            notice = workflow_hook.check_workflow_updates(
                self._cfg(enabled=True), self.project)
        finally:
            workflow_hook._git = orig
        self.assertIsNone(notice)


class TestMainBranchDetection(BaseCase):
    """`stop_hook.main_branch` auto-detection (explicit pin > detect > 'main')."""

    def _cfg(self, **stop_hook):
        return {
            "project_root": ".",
            "source_directories": ["src"],
            "documentation_directories": ["docs"],
            "ledger": {"directory": "history"},
            "env_check": {"tool_paths": {}},
            "stop_hook": stop_hook,
        }

    def _stub_git(self, responses):
        """Patch ``_git`` with a dict of arg-tuple-prefix -> return value."""
        calls = []

        def fake_git(root, *args):
            calls.append(args)
            for prefix, value in responses.items():
                if args[:len(prefix)] == prefix:
                    return value
            return None

        orig = workflow_hook._git
        workflow_hook._git = fake_git
        self.addCleanup(lambda: setattr(workflow_hook, "_git", orig))
        return calls

    def test_explicit_main_branch_wins_and_skips_detection(self):
        calls = self._stub_git({("symbolic-ref",): "origin/master"})
        branch = workflow_hook.resolve_main_branch(
            self._cfg(main_branch="trunk"), self.project)
        self.assertEqual(branch, "trunk")
        self.assertEqual(calls, [])  # no probe at all

    def test_blank_main_branch_falls_through_to_detection(self):
        self._stub_git({("symbolic-ref",): "origin/master"})
        branch = workflow_hook.resolve_main_branch(
            self._cfg(main_branch="   "), self.project)
        self.assertEqual(branch, "master")

    def test_detects_from_local_remote_head_ref(self):
        self._stub_git({("symbolic-ref",): "origin/develop"})
        self.assertEqual(
            workflow_hook.resolve_main_branch(self._cfg(), self.project), "develop")

    def test_detection_makes_no_network_call_by_default(self):
        calls = self._stub_git({})  # every probe fails
        branch = workflow_hook.resolve_main_branch(self._cfg(), self.project)
        self.assertEqual(branch, workflow_hook.DEFAULT_MAIN_BRANCH)
        self.assertNotIn(("remote", "show", "origin"), calls)

    def test_remote_show_fallback_only_when_opted_in(self):
        self._stub_git({("remote", "show"): (
            "* remote origin\n  Fetch URL: x\n  HEAD branch: master\n")})
        self.assertEqual(
            workflow_hook.resolve_main_branch(
                self._cfg(main_branch_probe_remote=True), self.project),
            "master")

    def test_remote_show_unknown_head_falls_back_to_default(self):
        self._stub_git({("remote", "show"): "  HEAD branch: (unknown)\n"})
        self.assertEqual(
            workflow_hook.resolve_main_branch(
                self._cfg(main_branch_probe_remote=True), self.project),
            workflow_hook.DEFAULT_MAIN_BRANCH)

    def test_autodetect_disabled_uses_default(self):
        calls = self._stub_git({("symbolic-ref",): "origin/master"})
        self.assertEqual(
            workflow_hook.resolve_main_branch(
                self._cfg(main_branch_autodetect=False), self.project),
            workflow_hook.DEFAULT_MAIN_BRANCH)
        self.assertEqual(calls, [])

    def test_custom_remote_name_is_used(self):
        calls = self._stub_git({("symbolic-ref",): "upstream/trunk"})
        self.assertEqual(
            workflow_hook.resolve_main_branch(
                self._cfg(main_branch_remote="upstream"), self.project), "trunk")
        self.assertEqual(
            calls[0], ("symbolic-ref", "--short", "refs/remotes/upstream/HEAD"))

    def test_result_is_memoised_in_state(self):
        calls = self._stub_git({("symbolic-ref",): "origin/master"})
        state = workflow_hook.default_state()
        cfg = self._cfg()
        self.assertEqual(workflow_hook.resolve_main_branch(cfg, self.project, state),
                         "master")
        self.assertEqual(state["main_branch_detected"], "master")
        # Second call re-uses the cache instead of probing again.
        self.assertEqual(workflow_hook.resolve_main_branch(cfg, self.project, state),
                         "master")
        self.assertEqual(len(calls), 1)

    def test_stop_suppresses_commit_reminder_on_detected_main(self):
        """Dirty tree on `master` must not nag when master is the detected default."""
        self.write_config(self._cfg())  # no explicit main_branch
        workflow_hook.save_state(self.session_id, workflow_hook.default_state())

        orig_status = workflow_hook.git_status
        workflow_hook.git_status = lambda root: {
            "branch": "master", "dirty": True, "ahead": None, "behind": None}
        self.addCleanup(lambda: setattr(workflow_hook, "git_status", orig_status))
        self._stub_git({("symbolic-ref",): "origin/master",
                        ("status",): " M src/a.py"})

        rc, out = run_hook({"hookEventName": "Stop", "session_id": self.session_id},
                           project_dir=self.project)
        self.assertIsNone(out)  # no commit reminder: master *is* main here
        # ...but the breadcrumb still lands, and the probe is persisted.
        self.assertTrue((self.project / "plans" / "UNFINISHED.md").is_file())
        self.assertEqual(
            workflow_hook.load_state(self.session_id)["main_branch_detected"],
            "master")

    def test_stop_still_reminds_on_feature_branch_with_detection(self):
        self.write_config(self._cfg())
        workflow_hook.save_state(self.session_id, workflow_hook.default_state())

        orig_status = workflow_hook.git_status
        workflow_hook.git_status = lambda root: {
            "branch": "feat/x", "dirty": True, "ahead": None, "behind": None}
        self.addCleanup(lambda: setattr(workflow_hook, "git_status", orig_status))
        self._stub_git({("symbolic-ref",): "origin/master",
                        ("status",): " M src/a.py"})

        rc, out = run_hook({"hookEventName": "Stop", "session_id": self.session_id},
                           project_dir=self.project)
        self.assertEqual(out["decision"], "block")
        self.assertIn("feat/x", out["reason"])


class TestDryRun(BaseCase):
    def test_dry_run_does_not_mutate_state(self):
        rc, out = run_hook(self.edit_event("src/a.py"), argv=["--dry-run"],
                           project_dir=self.project)
        # Output still computed...
        self.assertIsNotNone(out)
        # ...but no state file written for this session.
        self.assertFalse(workflow_hook.state_path(self.session_id).exists())


class TestLoopDetection(BaseCase):
    """Repeated identical tool calls (v14 section 15.4). Advisory, never blocking."""

    def bash_event(self, command):
        return {"hookEventName": "PostToolUse", "session_id": self.session_id,
                "tool_name": "Bash", "tool_input": {"command": command}}

    def enable_loops(self, **overrides):
        cfg = {
            "project_root": ".",
            "ledger": {"enabled": True, "directory": "history"},
            "source_directories": ["src"],
            "documentation_directories": ["docs"],
            "env_check": {"tool_paths": {}},
            "stop_hook": {"max_blocks": 2, "main_branch": "main"},
            "loop_detection": {"enabled": True, "repeat_threshold": 3,
                               "log_path": "metrics/loop.jsonl"},
        }
        cfg["loop_detection"].update(overrides)
        self.write_config(cfg)
        return self.project / "metrics" / "loop.jsonl"

    def test_below_threshold_is_silent(self):
        self.enable_loops()
        for _ in range(2):
            rc, out = run_hook(self.bash_event("pytest -q"), project_dir=self.project)
            self.assertEqual(rc, 0)
            self.assertIsNone(out)

    def test_fires_once_at_threshold_and_logs(self):
        log = self.enable_loops()
        for _ in range(2):
            run_hook(self.bash_event("pytest -q"), project_dir=self.project)

        rc, out = run_hook(self.bash_event("pytest -q"), project_dir=self.project)
        self.assertEqual(rc, 0)
        self.assertIsNotNone(out)
        self.assertIn("3x in a row", out["hookSpecificOutput"]["additionalContext"])

        # Exactly one JSONL record, carrying the run length.
        self.assertTrue(log.is_file())
        records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["repeat_count"], 3)
        self.assertEqual(records[0]["tool_name"], "Bash")

        # A fourth identical call must not re-report the same signature.
        rc, out = run_hook(self.bash_event("pytest -q"), project_dir=self.project)
        self.assertIsNone(out)
        self.assertEqual(len(log.read_text(encoding="utf-8").splitlines()), 1)

    def test_different_arguments_reset_the_run(self):
        self.enable_loops()
        for cmd in ("a", "a", "b", "a", "a"):
            rc, out = run_hook(self.bash_event(cmd), project_dir=self.project)
            self.assertIsNone(out, f"unexpected advisory after {cmd!r}")

    def test_disabled_produces_nothing(self):
        log = self.enable_loops(enabled=False)
        for _ in range(5):
            rc, out = run_hook(self.bash_event("pytest -q"), project_dir=self.project)
            self.assertIsNone(out)
        self.assertFalse(log.exists())

    def test_threshold_below_two_is_clamped(self):
        # A threshold of 1 would fire on every single call; clamp to 2.
        self.enable_loops(repeat_threshold=1)
        rc, out = run_hook(self.bash_event("x"), project_dir=self.project)
        self.assertIsNone(out)
        rc, out = run_hook(self.bash_event("x"), project_dir=self.project)
        self.assertIsNotNone(out)

    def test_stop_reports_loops_seen_this_session(self):
        self.enable_loops()
        for _ in range(3):
            run_hook(self.bash_event("pytest -q"), project_dir=self.project)
        rc, out = run_hook({"hookEventName": "Stop", "session_id": self.session_id},
                           project_dir=self.project)
        self.assertIsNotNone(out)
        self.assertIn("Loop detection fired", out["reason"])

    def test_missing_config_block_defaults_to_enabled(self):
        # Regression: a config predating loop_detection must still work.
        for _ in range(2):
            run_hook(self.bash_event("pytest -q"), project_dir=self.project)
        rc, out = run_hook(self.bash_event("pytest -q"), project_dir=self.project)
        self.assertIsNotNone(out)
        self.assertIn("3x in a row", out["hookSpecificOutput"]["additionalContext"])


class TestSchemaValidator(unittest.TestCase):
    """The stdlib JSON Schema subset used by --self-test."""

    SCHEMA = {
        "type": "object",
        "additionalProperties": False,
        "required": ["name"],
        "properties": {
            "name": {"type": "string"},
            "count": {"type": "integer", "minimum": 2},
            "mode": {"type": "string", "enum": ["a", "b"]},
            "nested": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"flag": {"type": "boolean"}},
            },
            "items": {"type": "array", "items": {"type": "string"}},
            "nullable": {"type": ["string", "null"]},
        },
    }

    def errors(self, instance):
        return workflow_hook.validate_against_schema(instance, self.SCHEMA)

    def test_valid_instance(self):
        self.assertEqual(self.errors({
            "name": "x", "count": 3, "mode": "a",
            "nested": {"flag": True}, "items": ["p"], "nullable": None}), [])

    def test_missing_required_key(self):
        self.assertIn("missing required key 'name'", " ".join(self.errors({})))

    def test_unknown_key_rejected(self):
        self.assertIn("unknown key 'nope'", " ".join(self.errors({"name": "x", "nope": 1})))

    def test_wrong_type(self):
        self.assertIn("expected string", " ".join(self.errors({"name": 42})))

    def test_enum_and_minimum(self):
        joined = " ".join(self.errors({"name": "x", "mode": "z", "count": 1}))
        self.assertIn("is not one of", joined)
        self.assertIn("below the minimum", joined)

    def test_nested_and_array_errors_report_paths(self):
        joined = " ".join(self.errors({"name": "x", "nested": {"flag": "yes"},
                                       "items": ["ok", 5]}))
        self.assertIn("<root>.nested.flag", joined)
        self.assertIn("<root>.items[1]", joined)

    def test_booleans_are_not_integers(self):
        # bool is a subclass of int in Python; the validator must not be fooled.
        self.assertIn("expected integer", " ".join(self.errors({"name": "x", "count": True})))

    def test_shipped_configs_validate(self):
        schema = json.loads((REPO_ROOT / "schemas" / "config_schema.json").read_text(
            encoding="utf-8"))
        for rel in (".claude/workflow_config.json", "templates/workflow_config.json"):
            with self.subTest(config=rel):
                cfg = json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))
                self.assertEqual(workflow_hook.validate_against_schema(cfg, schema), [])


class TestSelfTest(BaseCase):
    """--self-test exits non-zero on validation failure only, never on low maturity."""

    def run_self_test(self):
        buf = io.StringIO()
        old_env = os.environ.get("CLAUDE_PROJECT_DIR")
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.project)
        try:
            with redirect_stdout(buf):
                rc = workflow_hook.main(["--self-test"])
        finally:
            if old_env is None:
                os.environ.pop("CLAUDE_PROJECT_DIR", None)
            else:
                os.environ["CLAUDE_PROJECT_DIR"] = old_env
        return rc, buf.getvalue()

    def test_valid_config_passes(self):
        rc, out = self.run_self_test()
        self.assertEqual(rc, 0)
        self.assertIn("RESULT: PASS", out)

    def test_low_maturity_still_passes(self):
        # A bare project has no prohibitions and no retrospective; that is a young
        # repository, not a broken one.
        rc, out = self.run_self_test()
        self.assertEqual(rc, 0)
        self.assertIn("Governance maturity: level", out)

    def test_unknown_root_key_is_allowed(self):
        # The root schema sets additionalProperties: true on purpose, so a project
        # can carry its own keys alongside the workflow's.
        self.write_config({"project_root": ".", "project_specific_key": True})
        rc, out = self.run_self_test()
        self.assertEqual(rc, 0)
        self.assertIn("RESULT: PASS", out)

    def test_invalid_config_fails_and_names_the_key(self):
        # Nested blocks *are* closed (additionalProperties: false), so a typo there
        # is a real error rather than an extension point.
        self.write_config({"project_root": ".",
                           "stop_hook": {"max_blocks": 2, "mian_branch": "main"}})
        rc, out = self.run_self_test()
        self.assertEqual(rc, 1)
        self.assertIn("RESULT: FAIL", out)
        self.assertIn("mian_branch", out)

    def test_wrong_type_fails(self):
        self.write_config({"project_root": ".", "source_directories": "not-a-list"})
        rc, out = self.run_self_test()
        self.assertEqual(rc, 1)
        self.assertIn("source_directories", out)

    def test_writes_maturity_tracker(self):
        self.write_config({
            "project_root": ".",
            "governance": {"library_root": ".ai", "maturity_tracker": "out/maturity.json"},
        })
        rc, _ = self.run_self_test()
        self.assertEqual(rc, 0)
        tracker = json.loads((self.project / "out" / "maturity.json").read_text(
            encoding="utf-8"))
        self.assertIn("maturity_level", tracker)
        self.assertIn("checks", tracker)

    def test_reports_missing_frontmatter(self):
        (self.project / "docs" / "naked.md").write_text("# no frontmatter\n", encoding="utf-8")
        rc, out = self.run_self_test()
        self.assertEqual(rc, 0)  # a warning, not a validation failure
        self.assertIn("naked.md", out)

    def test_prov_sidecars_are_exempt_from_frontmatter(self):
        (self.project / "docs" / "thing.json.prov.md").write_text(
            "# Provenance for thing.json\n", encoding="utf-8")
        rc, out = self.run_self_test()
        self.assertEqual(rc, 0)
        self.assertNotIn("thing.json.prov.md", out)


class TestApiKeyWarning(unittest.TestCase):
    def setUp(self):
        self.old = os.environ.get("ANTHROPIC_API_KEY")

    def tearDown(self):
        if self.old is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = self.old

    def test_silent_when_unset(self):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        self.assertIsNone(workflow_hook.api_key_warning())

    def test_warns_when_set(self):
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test"
        warning = workflow_hook.api_key_warning()
        self.assertIsNotNone(warning)
        self.assertIn("subscription", warning)


class TestTier0Guard(BaseCase):
    """`PreToolUse` guard behind the Tier-0 prohibitions.

    The guard exists because permission patterns cannot express "is this branch
    shared" -- so every test here is a case a `permissions.deny` pattern gets
    wrong: reordered arguments, the short flag, the other shell, a subcommand
    hiding behind `&&`.
    """

    def setUp(self):
        super().setUp()
        # An explicit main_branch pin wins over detection, so no test in this
        # class shells out to git unless it stubs _git deliberately.
        self.write_config({
            "project_root": ".",
            "source_directories": ["src"],
            "documentation_directories": ["docs"],
            "ledger": {"directory": "history"},
            "env_check": {"tool_paths": {}},
            "stop_hook": {"main_branch": "main"},
        })

    def shell_event(self, command, tool_name="Bash"):
        return {"hookEventName": "PreToolUse", "session_id": self.session_id,
                "tool_name": tool_name, "tool_input": {"command": command}}

    def decide(self, command, tool_name="Bash"):
        """Return (decision, reason) for ``command``; (None, None) when silent."""
        rc, out = run_hook(self.shell_event(command, tool_name),
                           project_dir=self.project)
        self.assertEqual(rc, 0, "the guard must never exit non-zero")
        if out is None:
            return None, None
        hso = out.get("hookSpecificOutput") or {}
        return hso.get("permissionDecision"), hso.get("permissionDecisionReason")

    # -- output shape ------------------------------------------------------ #
    def test_decision_uses_the_documented_output_shape(self):
        rc, out = run_hook(self.shell_event("git push --force origin main"),
                           project_dir=self.project)
        self.assertEqual(rc, 0)
        hso = out["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PreToolUse")
        self.assertIn(hso["permissionDecision"], ("deny", "ask"))
        self.assertTrue(hso["permissionDecisionReason"].strip())

    # -- guard_force_push -------------------------------------------------- #
    def test_force_push_to_main_is_denied(self):
        decision, reason = self.decide("git push --force origin main")
        self.assertEqual(decision, "deny")
        self.assertIn("prohibition-force-push-shared", reason)

    def test_force_push_to_a_topic_branch_is_allowed(self):
        self.assertEqual(self.decide("git push --force origin feat/x")[0], None)

    def test_force_flag_after_the_refspec_is_denied(self):
        # `Bash(git push --force*)` misses this; the whole reason for a parser.
        self.assertEqual(self.decide("git push origin main --force")[0], "deny")

    def test_short_force_flag_is_denied(self):
        self.assertEqual(self.decide("git push -f origin main")[0], "deny")

    def test_force_with_lease_is_still_a_force_push(self):
        self.assertEqual(
            self.decide("git push --force-with-lease origin main")[0], "deny")

    def test_plus_refspec_is_a_force_push(self):
        self.assertEqual(self.decide("git push origin +main")[0], "deny")

    def test_colon_refspec_resolves_to_its_destination(self):
        self.assertEqual(self.decide("git push --force origin HEAD:main")[0], "deny")
        self.assertEqual(self.decide("git push --force origin main:feat/x")[0], None)

    def test_non_forced_push_to_main_is_allowed(self):
        self.assertEqual(self.decide("git push origin main")[0], None)

    def test_powershell_gets_the_same_decision(self):
        # A Bash-only deny list would be bypassed by the other shell entirely.
        self.assertEqual(
            self.decide("git push --force origin main", tool_name="PowerShell")[0],
            "deny")

    def test_force_push_hidden_behind_a_subcommand_is_denied(self):
        self.assertEqual(
            self.decide("git status && git push --force origin main")[0], "deny")

    def test_bare_force_push_uses_the_current_branch(self):
        calls = []

        def fake_git(root, *args):
            calls.append(args)
            if args[:1] == ("rev-parse",):
                return "main"
            return None

        orig = workflow_hook._git
        workflow_hook._git = fake_git
        self.addCleanup(lambda: setattr(workflow_hook, "_git", orig))
        self.assertEqual(self.decide("git push --force")[0], "deny")
        self.assertTrue(calls, "current branch should have been resolved")

    def test_a_plain_command_never_shells_out_to_git(self):
        """Parse first, resolve second -- this runs before every shell command."""
        calls = []

        def fake_git(root, *args):
            calls.append(args)
            return None

        orig = workflow_hook._git
        workflow_hook._git = fake_git
        self.addCleanup(lambda: setattr(workflow_hook, "_git", orig))
        self.decide("python -m unittest discover -s tests")
        self.assertEqual(calls, [])

    # -- guard_protected_paths --------------------------------------------- #
    def test_deleting_the_ledger_is_denied(self):
        decision, reason = self.decide("rm -rf history/")
        self.assertEqual(decision, "deny")
        self.assertIn("prohibition-delete-ledger", reason)

    def test_deleting_the_plan_archive_is_denied(self):
        self.assertEqual(self.decide("git rm -r plans/archive")[0], "deny")

    def test_powershell_removal_of_the_ledger_is_denied(self):
        self.assertEqual(
            self.decide("Remove-Item -Recurse -Force history",
                        tool_name="PowerShell")[0],
            "deny")

    def test_deleting_an_unprotected_path_is_allowed(self):
        self.assertEqual(self.decide("rm -rf build/")[0], None)

    def test_reading_the_ledger_is_allowed(self):
        # The prohibition is against deletion; the ledger must stay readable.
        self.assertEqual(self.decide("cat history/2026-W32.md")[0], None)

    # -- guard_history_rewrite --------------------------------------------- #
    def test_amend_escalates_rather_than_blocking(self):
        decision, reason = self.decide("git commit --amend -m 'x'")
        self.assertEqual(decision, "ask")
        self.assertIn("prohibition-rewrite-published-history", reason)

    def test_rebase_escalates(self):
        self.assertEqual(self.decide("git rebase main")[0], "ask")

    def test_hard_reset_escalates(self):
        self.assertEqual(self.decide("git reset --hard HEAD~1")[0], "ask")

    def test_an_ordinary_commit_is_allowed(self):
        self.assertEqual(self.decide("git commit -m 'x'")[0], None)

    # -- guard_heredoc ------------------------------------------------------ #
    def test_heredoc_to_an_interpreter_escalates(self):
        # The mistake this rule came from was `python - <<'PY'`, not a commit.
        decision, reason = self.decide("python - <<'PY'\nprint(1)\nPY")
        self.assertEqual(decision, "ask")
        self.assertIn("rule-no-heredoc-stdin", reason)

    def test_here_string_escalates(self):
        self.assertEqual(self.decide("cat <<< 'hello'")[0], "ask")

    def test_commit_message_on_stdin_escalates(self):
        self.assertEqual(self.decide("git commit -F -")[0], "ask")
        self.assertEqual(self.decide("git commit --file=-")[0], "ask")
        self.assertEqual(self.decide("git commit -F /dev/stdin")[0], "ask")

    def test_commit_message_from_a_file_is_allowed(self):
        self.assertEqual(self.decide("git commit -F msg.txt")[0], None)

    def test_bare_commit_escalates(self):
        # A bare `git commit` opens an editor and hangs the session.
        self.assertEqual(self.decide("git commit")[0], "ask")

    def test_left_shift_is_not_a_heredoc(self):
        self.assertEqual(self.decide("python -c 'print(2 << 3)'")[0], None)

    # -- precedence, config and fail-soft ----------------------------------- #
    def test_deny_wins_over_ask_in_a_compound_command(self):
        self.assertEqual(
            self.decide("git commit --amend && git push --force origin main")[0],
            "deny")

    def test_guard_can_be_disabled(self):
        cfg = json.loads(
            (self.project / ".claude" / "workflow_config.json").read_text("utf-8"))
        cfg["tier0_guard"] = {"enabled": False}
        self.write_config(cfg)
        self.assertEqual(self.decide("git push --force origin main")[0], None)

    def test_extra_protected_branches_are_honoured(self):
        cfg = json.loads(
            (self.project / ".claude" / "workflow_config.json").read_text("utf-8"))
        cfg["tier0_guard"] = {"protected_branches": ["release"]}
        self.write_config(cfg)
        self.assertEqual(self.decide("git push --force origin release")[0], "deny")

    def test_non_shell_tools_are_ignored(self):
        rc, out = run_hook(
            {"hookEventName": "PreToolUse", "session_id": self.session_id,
             "tool_name": "Edit", "tool_input": {"file_path": "src/a.py"}},
            project_dir=self.project)
        self.assertEqual(rc, 0)
        self.assertIsNone(out)

    def test_missing_tool_input_is_silent(self):
        rc, out = run_hook(
            {"hookEventName": "PreToolUse", "session_id": self.session_id,
             "tool_name": "Bash"},
            project_dir=self.project)
        self.assertEqual(rc, 0)
        self.assertIsNone(out)

    def test_the_guard_never_writes_session_state(self):
        """It runs before every shell command; state churn would be constant."""
        state_file = workflow_hook.state_path(self.session_id)
        self.assertFalse(state_file.exists())
        self.decide("git push --force origin main")
        self.assertFalse(state_file.exists())


class TestMtimeFallback(BaseCase):
    """The Stop reminders must see work done outside Edit/Write/MultiEdit.

    `source_changed` and `ledger_touched` are set by `PostToolUse`, which only
    fires for the editing tools. A ledger appended by a shell redirect, or a
    source file rewritten by `sed -i`, is invisible to it -- so the reminder
    fires when the work *was* done, and stays silent when it wasn't. Both
    directions are wrong; the second is worse.
    """

    def setUp(self):
        super().setUp()
        (self.project / "plans").mkdir(exist_ok=True)
        self.write_config(self._cfg())
        self.ledger = workflow_hook.current_ledger_path(self._cfg(), self.project)
        self.ledger.parent.mkdir(parents=True, exist_ok=True)

    def _cfg(self, **stop_hook):
        stop_hook.setdefault("main_branch", "main")
        return {
            "project_root": ".",
            "source_directories": ["src"],
            "documentation_directories": ["docs"],
            "ledger": {"directory": "history"},
            "env_check": {"tool_paths": {}},
            "stop_hook": stop_hook,
        }

    def _age(self, path, seconds_before_session):
        """Backdate or forward-date a file relative to this session's start."""
        state = workflow_hook.load_state(self.session_id)
        stamp = state["session_start_ts"] - seconds_before_session
        os.utime(path, (stamp, stamp))

    def _seed_session(self, **flags):
        state = workflow_hook.default_state()
        state.update(flags)
        workflow_hook.save_state(self.session_id, state)
        return state

    def _stop(self):
        return run_hook({"hookEventName": "Stop", "session_id": self.session_id},
                        project_dir=self.project)

    def _reason(self, out):
        return (out or {}).get("reason", "")

    # -- the ledger half ---------------------------------------------------- #
    def test_ledger_written_outside_the_editing_tools_silences_the_reminder(self):
        self._seed_session(source_changed=True, ledger_touched=False)
        self.ledger.write_text("appended by a shell redirect\n", encoding="utf-8")
        self._age(self.ledger, -5)  # 5s after session start
        rc, out = self._stop()
        self.assertEqual(rc, 0)
        self.assertNotIn("ledger", self._reason(out).lower())

    def test_a_ledger_untouched_this_session_still_reminds(self):
        self._seed_session(source_changed=True, ledger_touched=False)
        self.ledger.write_text("written last week\n", encoding="utf-8")
        self._age(self.ledger, 86400)  # a day before session start
        rc, out = self._stop()
        self.assertIn("ledger", self._reason(out).lower())

    def test_a_missing_ledger_still_reminds(self):
        self._seed_session(source_changed=True, ledger_touched=False)
        rc, out = self._stop()
        self.assertIn("ledger", self._reason(out).lower())

    # -- the source half, the more dangerous direction ---------------------- #
    def test_source_changed_outside_the_editing_tools_raises_the_reminder(self):
        """`sed -i` on a source file must not buy silence."""
        self._seed_session(source_changed=False, ledger_touched=False)
        touched = self.project / "src" / "rewritten_by_sed.py"
        touched.write_text("x = 1\n", encoding="utf-8")
        self._age(touched, -5)
        rc, out = self._stop()
        self.assertIn("ledger", self._reason(out).lower())

    def test_untouched_source_stays_silent(self):
        self._seed_session(source_changed=False, ledger_touched=False)
        stale = self.project / "src" / "old.py"
        stale.write_text("x = 1\n", encoding="utf-8")
        self._age(stale, 86400)
        rc, out = self._stop()
        self.assertNotIn("ledger", self._reason(out).lower())

    # -- config, pruning and bounds ----------------------------------------- #
    def test_fallback_can_be_disabled(self):
        self.write_config(self._cfg(mtime_fallback=False))
        self._seed_session(source_changed=True, ledger_touched=False)
        self.ledger.write_text("appended\n", encoding="utf-8")
        self._age(self.ledger, -5)
        rc, out = self._stop()
        self.assertIn("ledger", self._reason(out).lower())  # falls back to the flag

    def test_pruned_directories_are_not_scanned(self):
        self._seed_session(source_changed=False, ledger_touched=False)
        noisy = self.project / "src" / "__pycache__"
        noisy.mkdir()
        artefact = noisy / "old.pyc"
        artefact.write_text("compiled\n", encoding="utf-8")
        self._age(artefact, -5)
        rc, out = self._stop()
        self.assertNotIn("ledger", self._reason(out).lower())

    def test_extra_prune_names_are_honoured(self):
        self.write_config(self._cfg(mtime_prune=["vendor"]))
        self._seed_session(source_changed=False, ledger_touched=False)
        vendored = self.project / "src" / "vendor"
        vendored.mkdir()
        artefact = vendored / "lib.py"
        artefact.write_text("x = 1\n", encoding="utf-8")
        self._age(artefact, -5)
        rc, out = self._stop()
        self.assertNotIn("ledger", self._reason(out).lower())

    def test_scan_limit_bounds_the_walk(self):
        """The walk runs at every Stop; the worst case must be bounded."""
        seen = workflow_hook.changed_since(
            ["src"], threshold=0, project_root=self.project, limit=0)
        self.assertFalse(seen, "limit=0 must scan nothing and report nothing")

    def test_changed_since_exits_on_the_first_hit(self):
        state = self._seed_session()
        for i in range(5):
            f = self.project / "src" / f"f{i}.py"
            f.write_text("x\n", encoding="utf-8")
        self.assertTrue(workflow_hook.changed_since(
            ["src"], state["session_start_ts"] - 60, self.project, limit=1))

    def test_current_ledger_path_follows_the_configured_directory(self):
        cfg = {"ledger": {"directory": "changelog"}}
        path = workflow_hook.current_ledger_path(cfg, self.project)
        self.assertEqual(path.parent.name, "changelog")
        self.assertRegex(path.name, r"^\d{4}-W\d{2}\.md$")


class TestBreadcrumbNotCountedAsWork(BaseCase):
    """An auto-breadcrumb must not be read as the work it reports.

    `handle_stop` writes plans/UNFINISHED.md when the tree is dirty. That file
    is itself untracked, so the next Stop sees it in `git status --porcelain`
    and treats it as more unfinished work -- a loop that manufactures the state
    it complains about, and which can never clear on its own. The marker the
    breadcrumb already carries (to avoid clobbering a human plan) is reused to
    tell the two apart.
    """

    def setUp(self):
        super().setUp()
        (self.project / "plans").mkdir(exist_ok=True)
        # A real repo, so the porcelain line format is exercised rather than
        # mocked -- the parsing is where this would break.
        for args in (["init", "-q"], ["config", "user.email", "t@example.com"],
                     ["config", "user.name", "t"]):
            subprocess.run(["git"] + args, cwd=str(self.project),
                           capture_output=True, text=True)
        (self.project / ".gitignore").write_text("", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=str(self.project),
                       capture_output=True, text=True)
        subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=str(self.project),
                       capture_output=True, text=True)

    def _breadcrumb(self, marked=True):
        target = self.project / "plans" / "UNFINISHED.md"
        head = workflow_hook.BREADCRUMB_MARKER + "\n" if marked else ""
        target.write_text(head + "# something\n", encoding="utf-8")
        return target

    def test_marked_breadcrumb_is_not_dirt(self):
        self._breadcrumb(marked=True)
        self.assertFalse(
            workflow_hook.dirty_excluding_breadcrumb(self.project),
            "a tree whose only change is the hook's own breadcrumb is not dirty")

    def test_human_plan_at_the_same_path_is_dirt(self):
        self._breadcrumb(marked=False)
        self.assertTrue(
            workflow_hook.dirty_excluding_breadcrumb(self.project),
            "a human-authored plan is real uncommitted work")

    def test_other_changes_alongside_a_breadcrumb_still_count(self):
        self._breadcrumb(marked=True)
        (self.project / "src" / "new.py").write_text("x = 1\n", encoding="utf-8")
        self.assertTrue(workflow_hook.dirty_excluding_breadcrumb(self.project))

    def test_an_auto_breadcrumb_is_not_an_outstanding_plan(self):
        self._breadcrumb(marked=True)
        self.assertFalse(
            workflow_hook.has_outstanding_plan(self.project),
            "an auto-breadcrumb is a symptom of a dirty tree, not a plan owed")

    def test_a_human_plan_is_outstanding(self):
        self._breadcrumb(marked=False)
        self.assertTrue(workflow_hook.has_outstanding_plan(self.project))

    def test_no_file_means_no_outstanding_plan(self):
        self.assertFalse(workflow_hook.has_outstanding_plan(self.project))


class TestDocExclusion(BaseCase):
    """One predicate decides whether a doc is held to the frontmatter rule."""

    def _cfg(self, exclude=None):
        return {"documentation_directories": ["docs"],
                "documentation_exclude": exclude or []}

    def test_configured_prefix_is_excluded(self):
        doc = self.project / "docs" / "staging" / "draft.md"
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text("no frontmatter\n", encoding="utf-8")
        self.assertTrue(workflow_hook.is_excluded_doc(
            doc, self._cfg(["docs/staging"]), self.project))

    def test_unlisted_doc_is_not_excluded(self):
        doc = self.project / "docs" / "real.md"
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text("no frontmatter\n", encoding="utf-8")
        self.assertFalse(workflow_hook.is_excluded_doc(doc, self._cfg(), self.project))

    def test_exclude_from_ai_frontmatter_is_honoured(self):
        doc = self.project / "docs" / "CHANGELOG.md"
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text("---\nexclude_from_ai: true\n---\n\n# log\n", encoding="utf-8")
        self.assertTrue(workflow_hook.is_excluded_doc(doc, self._cfg(), self.project))

    def test_prov_sidecars_stay_excluded(self):
        doc = self.project / "docs" / "thing.prov.md"
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text("sidecar\n", encoding="utf-8")
        self.assertTrue(workflow_hook.is_excluded_doc(doc, self._cfg(), self.project))


class TestConfidenceDerivation(unittest.TestCase):
    """`confidence_level` is computed, never asserted.

    The protocol's determination table is a set of *thresholds* -- "authority
    >= 10 and consensus >= 3 and age > 5y" -- not exact keys, so (10, 4, 6)
    must also yield 5. A threshold ladder is exactly where an off-by-one hides,
    hence the boundary cases below.
    """

    def d(self, authority, consensus, age_days):
        return workflow_hook.derive_confidence(authority, consensus, age_days)

    def test_industry_standard(self):
        self.assertEqual(self.d(10, 3, 5 * 365 + 1), 5)

    def test_above_every_threshold_still_tops_out_at_five(self):
        self.assertEqual(self.d(10, 9, 20 * 365), 5)

    def test_enterprise_proven(self):
        self.assertEqual(self.d(9, 2, 3 * 365 + 1), 4)

    def test_community_validated(self):
        self.assertEqual(self.d(7, 1, 366), 3)

    def test_emerging(self):
        self.assertEqual(self.d(5, 1, 30), 2)

    def test_uncertain_when_nothing_supports_it(self):
        self.assertEqual(self.d(1, 0, 0), 1)

    def test_brand_new_item_cannot_reach_the_top(self):
        """Age is a required factor -- a day-old citation is not yet proven."""
        self.assertLess(self.d(10, 3, 0), 5)

    def test_no_consensus_caps_the_level(self):
        self.assertLess(self.d(10, 0, 10 * 365), 5)

    def test_boundaries_are_inclusive_on_the_documented_side(self):
        for authority, consensus, age, expected in (
            (10, 3, 5 * 365 + 1, 5),
            (9, 3, 5 * 365 + 1, 4),
            (10, 2, 5 * 365 + 1, 4),
            (8, 2, 3 * 365 + 1, 4),
            (7, 2, 3 * 365 + 1, 3),
        ):
            with self.subTest(a=authority, c=consensus, age=age):
                self.assertEqual(self.d(authority, consensus, age), expected)

    def test_matrix_is_ordered_strongest_first(self):
        levels = [row[-1] for row in workflow_hook.CONFIDENCE_MATRIX]
        self.assertEqual(levels, sorted(levels, reverse=True),
                         "an unordered ladder would return the wrong level")


class TestEnforcementModeMatchesGuard(unittest.TestCase):
    """An artifact's declared `enforcement_mode` must equal what its guard returns.

    `enforced_by` proves the guard exists; it says nothing about whether the
    guard denies or merely asks. Those are different strengths -- an ask can be
    waved through -- so the artifact declares which one it is, and this binds
    that declaration to the code the same way `resolve_enforcer` binds the
    enforcer name. Flip an artifact to "ask" while its guard still denies and
    this fails.
    """

    # One command per guard that must trip it.
    TRIPWIRES = {
        "guard_force_push": "git push --force origin main",
        "guard_protected_paths": "rm -rf history/",
        "guard_history_rewrite": "git commit --amend",
        "guard_heredoc": "python - <<'PY'",
    }

    def setUp(self):
        self.artifacts = []
        root = REPO_ROOT / ".ai"
        for path in sorted(root.rglob("rule-*.json")) + sorted(
                root.rglob("prohibition-*.json")):
            self.artifacts.append((path, json.loads(path.read_text(encoding="utf-8"))))

    def _guard_decision(self, guard_name):
        command = self.TRIPWIRES[guard_name]
        guard = getattr(workflow_hook, guard_name)
        tokens = command.split()
        if guard_name == "guard_force_push":
            finding = guard(tokens, lambda: {"main"}, lambda: "main")
        elif guard_name == "guard_protected_paths":
            finding = guard(tokens, ["history", "plans/archive"])
        elif guard_name == "guard_heredoc":
            finding = guard(tokens, command)
        else:
            finding = guard(tokens)
        self.assertIsNotNone(
            finding, f"{guard_name} did not fire on its own tripwire: {command!r}")
        return finding[0]

    def test_every_tripwire_actually_trips(self):
        for guard_name in self.TRIPWIRES:
            with self.subTest(guard=guard_name):
                self.assertIn(self._guard_decision(guard_name), ("deny", "ask"))

    def test_declared_mode_matches_what_the_guard_returns(self):
        checked = 0
        for path, artifact in self.artifacts:
            for reference in artifact.get("enforced_by") or []:
                guard_name = str(reference).rsplit("::", 1)[-1]
                if guard_name not in self.TRIPWIRES:
                    continue
                checked += 1
                with self.subTest(artifact=path.name, guard=guard_name):
                    self.assertEqual(
                        self._guard_decision(guard_name),
                        artifact.get("enforcement_mode"),
                        f"{path.name} declares enforcement_mode "
                        f"{artifact.get('enforcement_mode')!r} but {guard_name} "
                        "returns something else")
        self.assertEqual(
            checked, len(self.TRIPWIRES),
            "every guard should back exactly one artifact; if that changed, "
            "update TRIPWIRES rather than loosening this assertion")


if __name__ == "__main__":
    unittest.main()
