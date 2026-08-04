#!/usr/bin/env python3
"""Integrity tests for the governance library under ``.ai/``.

Stdlib ``unittest`` only -- run with::

    python -m unittest discover -s tests
    # or
    python -m unittest tests.test_governance_library

``tests/test_hook.py`` covers the *dispatcher*. This module covers the *library*:
the checklist artifacts the dispatcher's rules are written down in. Every
assertion here is an invariant the library already claims in prose -- in
``.ai/GROWTH.md``, ``.ai/README.md`` and ``GUIDE.md`` section 12 -- turned into
something that fails a build instead of merely reading well.

The load-bearing one is :class:`EnforcementHonesty`. GROWTH.md says "if you
cannot name which hook or test makes it *live*, it is not live"; this module
makes that mechanical by requiring every ``live`` artifact to carry an
``enforced_by`` list whose every entry resolves to a real function, test or
workflow file. A tier claim that cannot be traced to code now fails.

These tests read the real library rather than fixtures -- there is nothing to
mock, and a fixture would only test the fixture.
"""

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LIBRARY = REPO_ROOT / ".ai"
TEMPLATE = REPO_ROOT / "templates" / "ai-library"

TIERS = ("live", "convention", "declarative")

# The CISA five-risk framework the library claims to instantiate, with the
# weight band each source is defined over. Source of truth:
# docs/self-growing-checklist-ecosystem/03-risk-gates-and-metrics.md section 11.3.
# Declared once here and cross-checked against .ai/GROWTH.md by
# ``RiskTaxonomy.test_growth_doc_documents_the_same_taxonomy`` so the table and
# the doc cannot drift apart.
RISK_BANDS = {
    "component": (1, 3),
    "design": (4, 6),
    "capability": (7, 10),
    "structural": (6, 9),
    "accountability": (8, 10),
}

# Keys GROWTH.md requires on every rule and prohibition file.
REQUIRED_ARTIFACT_KEYS = (
    "id", "enforcement", "enforcement_status", "risk_source", "risk_weight",
    "provenance",
)

# `.ai/` and `templates/ai-library/` are the same library; the template carries
# adopter placeholders in exactly these files and must match everywhere else.
# Listed one path per line so widening the exemption is a visible decision in a
# diff rather than a silent loosening of the parity check.
PARITY_EXEMPT = frozenset({
    "README.md",
    "00-system/agent-registry.json",
    "00-system/governance.yaml",
    "00-system/maturity-tracker.json",
    "00-system/team-members.json",
})


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def phase_rules():
    return sorted((LIBRARY / "01-phases").glob("rule-*.json"))


def prohibitions():
    return sorted((LIBRARY / "02-market-rules" / "prohibitions").glob("prohibition-*.json"))


def artifacts():
    """Every rule and prohibition file, as (relative path, parsed dict) pairs."""
    return [(p.relative_to(REPO_ROOT).as_posix(), load_json(p))
            for p in phase_rules() + prohibitions()]


def manifests():
    return sorted(LIBRARY.rglob("manifest.json"))


def all_library_json():
    """Every JSON file in the library, manifests and rule files included."""
    return sorted(LIBRARY.rglob("*.json"))


def walk_objects(node):
    """Yield every dict nested anywhere inside ``node``, including ``node``."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk_objects(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk_objects(item)


def relative_files(root):
    """Every file under ``root`` as a set of posix-style relative paths."""
    return {p.relative_to(root).as_posix()
            for p in root.rglob("*") if p.is_file()}


# --- enforced_by resolution ------------------------------------------------- #
# Deliberately regex over the source text rather than an AST walk or an import:
# the reference must survive harmless reformatting, and a test that imports the
# hook to introspect it would couple tier claims to import side effects.
_SOURCE_CACHE = {}


def _source(rel_path):
    if rel_path not in _SOURCE_CACHE:
        path = REPO_ROOT / rel_path
        _SOURCE_CACHE[rel_path] = path.read_text(encoding="utf-8") if path.is_file() else None
    return _SOURCE_CACHE[rel_path]


def resolve_enforcer(reference):
    """Return an error string if ``reference`` names nothing real, else ``None``.

    Accepted forms::

        hooks/workflow_hook.py::handle_stop        function must exist
        tests/test_hook.py::StopTests              class must exist
        tests/test_hook.py::StopTests::test_foo    class and method must exist
        .github/workflows/tests.yml                file must exist
    """
    rel_path, _, symbol_path = reference.partition("::")
    target = REPO_ROOT / rel_path
    if not target.is_file():
        return f"{reference}: {rel_path} does not exist"
    if not symbol_path:
        return None

    source = _source(rel_path)
    if source is None:
        return f"{reference}: {rel_path} is not readable as text"

    for symbol in symbol_path.split("::"):
        keyword = "class" if symbol[:1].isupper() else "def"
        if not re.search(rf"^\s*{keyword} {re.escape(symbol)}\b", source, re.MULTILINE):
            return f"{reference}: no `{keyword} {symbol}` in {rel_path}"
    return None


# --------------------------------------------------------------------------- #
# Manifests
# --------------------------------------------------------------------------- #
class ManifestIntegrity(unittest.TestCase):
    """A manifest that lies is worse than no manifest (.ai/GROWTH.md)."""

    def test_library_is_present(self):
        self.assertTrue(LIBRARY.is_dir(), f"{LIBRARY} missing")
        self.assertTrue(manifests(), "no manifest.json found in the library")

    def test_listed_files_exist(self):
        for manifest_path in manifests():
            manifest = load_json(manifest_path)
            for item in manifest.get("items") or []:
                with self.subTest(manifest=manifest_path.name, item=item.get("id")):
                    self.assertTrue(
                        (manifest_path.parent / item["file"]).is_file(),
                        f"{manifest_path}: lists {item['file']}, which does not exist")

    def test_total_items_matches_item_count(self):
        for manifest_path in manifests():
            manifest = load_json(manifest_path)
            if "total_items" not in manifest:
                continue
            with self.subTest(manifest=manifest_path.name):
                self.assertEqual(
                    manifest["total_items"], len(manifest.get("items") or []),
                    f"{manifest_path}: total_items disagrees with items")

    def test_no_orphan_files(self):
        """Every JSON beside a manifest is listed by it.

        The reverse of :meth:`test_listed_files_exist`, and the direction that
        actually catches a rule added to the folder but never registered.
        """
        for manifest_path in manifests():
            manifest = load_json(manifest_path)
            if "items" not in manifest:
                continue  # index-only manifest (e.g. 02-market-rules lists subfolders)
            listed = {item["file"] for item in manifest["items"]}
            on_disk = {p.name for p in manifest_path.parent.glob("*.json")
                       if p.name != "manifest.json"}
            with self.subTest(manifest=manifest_path.name):
                self.assertEqual(
                    set(), on_disk - listed,
                    f"{manifest_path}: files present but unlisted")

    def test_ids_match_filenames(self):
        for manifest_path in manifests():
            for item in load_json(manifest_path).get("items") or []:
                with self.subTest(manifest=manifest_path.name, item=item.get("id")):
                    self.assertEqual(
                        item["id"], Path(item["file"]).stem,
                        f"{manifest_path}: id and filename disagree")

    def test_declared_subfolders_exist(self):
        for manifest_path in manifests():
            for sub in load_json(manifest_path).get("subfolders") or []:
                with self.subTest(manifest=manifest_path.name, subfolder=sub):
                    self.assertTrue((manifest_path.parent / sub).is_dir(),
                                    f"{manifest_path}: subfolder {sub} missing")

    def test_manifest_tier_matches_the_rule_file(self):
        """The phase manifest is an index, not a second opinion."""
        manifest_path = LIBRARY / "01-phases" / "manifest.json"
        for item in load_json(manifest_path)["items"]:
            rule = load_json(manifest_path.parent / item["file"])
            with self.subTest(rule=item["id"]):
                self.assertEqual(
                    rule["enforcement_status"], item["enforcement_status"],
                    f"{item['id']}: manifest says {item['enforcement_status']}, "
                    f"the rule file says {rule['enforcement_status']}")

    def test_manifest_step_matches_the_rule_file(self):
        manifest_path = LIBRARY / "01-phases" / "manifest.json"
        for item in load_json(manifest_path)["items"]:
            rule = load_json(manifest_path.parent / item["file"])
            with self.subTest(rule=item["id"]):
                self.assertEqual(
                    rule.get("maps_to_v14_step"), item.get("v14_step"),
                    f"{item['id']}: manifest and rule file disagree on the v14 step")


# --------------------------------------------------------------------------- #
# Rule / prohibition schema
# --------------------------------------------------------------------------- #
class RuleSchema(unittest.TestCase):
    def test_artifacts_exist(self):
        self.assertTrue(phase_rules(), "no phase rules found")
        self.assertTrue(prohibitions(), "no prohibitions found")

    def test_required_keys_present(self):
        for name, artifact in artifacts():
            for key in REQUIRED_ARTIFACT_KEYS:
                with self.subTest(artifact=name, key=key):
                    self.assertIn(key, artifact, f"{name}: missing '{key}'")

    def test_id_matches_filename(self):
        for path in phase_rules() + prohibitions():
            with self.subTest(artifact=path.name):
                self.assertEqual(load_json(path)["id"], path.stem)

    def test_provenance_is_populated(self):
        for name, artifact in artifacts():
            with self.subTest(artifact=name):
                provenance = artifact.get("provenance")
                self.assertIsInstance(provenance, dict, f"{name}: provenance must be an object")
                self.assertTrue(provenance.get("source"), f"{name}: provenance.source is empty")

    def test_enforcement_status_is_a_known_tier(self):
        for name, artifact in artifacts():
            with self.subTest(artifact=name):
                self.assertIn(artifact["enforcement_status"], TIERS, f"{name}: unknown tier")

    def test_prohibitions_are_tier_zero_and_absolute(self):
        for path in prohibitions():
            artifact = load_json(path)
            with self.subTest(artifact=path.name):
                self.assertEqual(0, artifact.get("tier"), f"{path.name}: not tier 0")
                self.assertEqual("ABSOLUTE", artifact.get("enforcement"))
                self.assertIs(False, artifact.get("overrideable"),
                              f"{path.name}: a tier-0 prohibition is never overrideable")


# --------------------------------------------------------------------------- #
# Risk taxonomy
# --------------------------------------------------------------------------- #
class RiskTaxonomy(unittest.TestCase):
    def test_risk_source_is_in_the_taxonomy(self):
        for name, artifact in artifacts():
            with self.subTest(artifact=name):
                self.assertIn(
                    artifact["risk_source"], RISK_BANDS,
                    f"{name}: risk_source {artifact['risk_source']!r} is not one of the "
                    f"CISA five {sorted(RISK_BANDS)}")

    def test_risk_weight_is_in_band_or_carries_a_note(self):
        """An out-of-band weight must be argued for, not silently retuned.

        Nudging an honestly-assessed number until it clears an imported
        threshold is the same failure as claiming enforcement that does not
        exist, so the escape hatch is a written reason rather than a new number.
        """
        for name, artifact in artifacts():
            source = artifact["risk_source"]
            if source not in RISK_BANDS:
                continue  # reported by the test above
            low, high = RISK_BANDS[source]
            weight = artifact["risk_weight"]
            with self.subTest(artifact=name):
                self.assertIsInstance(weight, int, f"{name}: risk_weight must be an integer")
                if low <= weight <= high:
                    continue
                self.assertTrue(
                    (artifact.get("risk_weight_note") or "").strip(),
                    f"{name}: risk_weight {weight} is outside the {source} band "
                    f"{low}-{high} and carries no risk_weight_note explaining why")

    def test_note_is_absent_when_the_weight_is_in_band(self):
        """No unearned notes -- a note means a real, argued deviation."""
        for name, artifact in artifacts():
            source = artifact["risk_source"]
            if source not in RISK_BANDS:
                continue
            low, high = RISK_BANDS[source]
            if low <= artifact["risk_weight"] <= high:
                with self.subTest(artifact=name):
                    self.assertIsNone(
                        artifact.get("risk_weight_note"),
                        f"{name}: weight is inside the {source} band; drop the note")

    def test_growth_doc_documents_the_same_taxonomy(self):
        """.ai/GROWTH.md tells authors which sources are legal -- it must be right."""
        text = (LIBRARY / "GROWTH.md").read_text(encoding="utf-8")
        for source in RISK_BANDS:
            with self.subTest(source=source):
                self.assertIn(f"`{source}`", text,
                              f"GROWTH.md does not document the {source!r} risk source")
        for invented in ("`privilege`", "`behavioral`"):
            with self.subTest(source=invented):
                self.assertNotIn(
                    invented, text,
                    f"GROWTH.md documents {invented}, which is not in the CISA taxonomy")


# --------------------------------------------------------------------------- #
# Enforcement honesty -- the load-bearing check
# --------------------------------------------------------------------------- #
class EnforcementHonesty(unittest.TestCase):
    """"If you cannot name which hook or test makes it live, it is not live."""

    def test_live_artifacts_name_an_enforcer(self):
        for name, artifact in artifacts():
            if artifact["enforcement_status"] != "live":
                continue
            with self.subTest(artifact=name):
                enforcers = artifact.get("enforced_by")
                self.assertIsInstance(
                    enforcers, list,
                    f"{name}: claims 'live' but has no enforced_by list")
                self.assertTrue(enforcers, f"{name}: claims 'live' with an empty enforced_by")

    def test_named_enforcers_resolve(self):
        for name, artifact in artifacts():
            for reference in artifact.get("enforced_by") or []:
                with self.subTest(artifact=name, enforcer=reference):
                    self.assertIsNone(resolve_enforcer(reference),
                                      resolve_enforcer(reference))

    def test_non_live_artifacts_do_not_name_an_enforcer(self):
        """A convention that names an enforcer is either under-tiered or bluffing."""
        for name, artifact in artifacts():
            if artifact["enforcement_status"] == "live":
                continue
            with self.subTest(artifact=name):
                self.assertIsNone(
                    artifact.get("enforced_by"),
                    f"{name}: is '{artifact['enforcement_status']}' but names an enforcer -- "
                    "promote it to 'live' or drop the claim")

    def test_conventions_explain_what_is_missing(self):
        """A convention should say what stops it being live, not just assert itself."""
        for name, artifact in artifacts():
            if artifact["enforcement_status"] != "convention":
                continue
            with self.subTest(artifact=name):
                self.assertTrue(
                    (artifact.get("enforcement_note") or "").strip(),
                    f"{name}: 'convention' needs an enforcement_note saying what is "
                    "not enforced and what the real mechanism is")


class EnforcementStrength(unittest.TestCase):
    """`live` covers two strengths, and the artifact must say which it has.

    A guard that returns ``deny`` blocks outright. One that returns ``ask``
    blocks until a human answers -- and the human may wave it through, which
    happened within an hour of the guard shipping. Both are `live` under this
    library's own definition, but they are not the same promise, so the stronger
    reading must not be the default. ``tests/test_hook.py`` holds the declared
    mode against what the guard actually returns.
    """

    MODES = ("deny", "ask")

    @staticmethod
    def _guard_backed(artifact):
        return any("::guard_" in str(ref)
                   for ref in (artifact.get("enforced_by") or []))

    def test_guard_backed_artifacts_declare_a_mode(self):
        for name, artifact in artifacts():
            if not self._guard_backed(artifact):
                continue
            with self.subTest(artifact=name):
                self.assertIn(
                    artifact.get("enforcement_mode"), self.MODES,
                    f"{name}: enforced by a guard but does not declare whether it "
                    "denies or asks -- `live` alone overstates an ask")

    def test_mode_is_absent_when_no_guard_backs_the_artifact(self):
        """No unearned modes -- the field means a guard really decides this."""
        for name, artifact in artifacts():
            if self._guard_backed(artifact):
                continue
            with self.subTest(artifact=name):
                self.assertIsNone(
                    artifact.get("enforcement_mode"),
                    f"{name}: declares an enforcement_mode but names no guard, so "
                    "nothing produces that decision")


class TierVocabulary(unittest.TestCase):
    """The tier rules apply to every JSON object in the library, not just rules.

    Generalised on purpose: ``00-system/`` carries tier claims on nested blocks
    (``reversibility``, ``loop_detection``, ``cross_session_risk``, ...) that no
    per-file check would reach, and a keyword list would go stale the moment a
    new block is added.
    """

    def _tiered_objects(self):
        for path in all_library_json():
            # Manifests restate a rule's tier as an index entry; requiring the
            # enforcer there too would mean maintaining the same fact twice,
            # which is the drift this module exists to prevent. The index is
            # tied to the rule file by ManifestIntegrity instead.
            if path.name == "manifest.json":
                continue
            for obj in walk_objects(load_json(path)):
                if "enforcement_status" in obj:
                    yield path.relative_to(REPO_ROOT).as_posix(), obj

    def test_every_tier_claim_uses_a_known_tier(self):
        for name, obj in self._tiered_objects():
            with self.subTest(file=name, tier=obj["enforcement_status"]):
                self.assertIn(obj["enforcement_status"], TIERS,
                              f"{name}: unknown tier {obj['enforcement_status']!r}")

    def test_every_live_claim_names_a_resolvable_enforcer(self):
        for name, obj in self._tiered_objects():
            if obj.get("enforcement_status") != "live":
                continue
            with self.subTest(file=name, claim=obj.get("id") or sorted(obj)[:3]):
                enforcers = obj.get("enforced_by")
                self.assertTrue(
                    isinstance(enforcers, list) and enforcers,
                    f"{name}: a 'live' claim with no enforced_by")
                for reference in enforcers:
                    self.assertIsNone(resolve_enforcer(reference),
                                      resolve_enforcer(reference))


class DeclarativeHonesty(unittest.TestCase):
    """Declarative fields are null with a reason attached, never plausible fakes."""

    # Metadata that may sit alongside a declarative block without being a value.
    METADATA_KEYS = frozenset({"enforcement_status", "reason", "note", "see",
                               "enforcement_note", "schema_note"})

    def _declarative_objects(self):
        for path in all_library_json():
            for obj in walk_objects(load_json(path)):
                if obj.get("enforcement_status") == "declarative":
                    yield path.relative_to(REPO_ROOT).as_posix(), obj

    def test_declarative_blocks_state_a_reason(self):
        for name, obj in self._declarative_objects():
            with self.subTest(file=name):
                self.assertTrue(
                    (obj.get("reason") or "").strip(),
                    f"{name}: declarative block with no reason -- say why it cannot be enforced")

    def test_declarative_values_stay_empty(self):
        """Populating a placeholder must break the build, not read as verified.

        Guards ``agent-registry.json``'s identity block in particular: `did`,
        `spiffe_id` and `public_key` are null because there is no key
        infrastructure here, and ``did:trail`` itself is recorded as
        independently unverified in docs/governance-integration-decision.md.
        """
        for name, obj in self._declarative_objects():
            for key, value in obj.items():
                if key in self.METADATA_KEYS or key.endswith("_note"):
                    continue
                with self.subTest(file=name, key=key):
                    self.assertIn(
                        value, (None, [], {}, ""),
                        f"{name}: declarative field {key!r} is populated with {value!r} -- "
                        "either it is really enforced (re-tier it) or this is a fake")


# --------------------------------------------------------------------------- #
# v14 step mapping
# --------------------------------------------------------------------------- #
class StepMapping(unittest.TestCase):
    """The GUIDE section 12 table and the phase manifest are one claim, stated twice."""

    @staticmethod
    def guide_table():
        """Parse GUIDE section 12 into {step number: tier}."""
        text = (REPO_ROOT / "GUIDE.md").read_text(encoding="utf-8")
        row = re.compile(r"^\|\s*(\d+)\s*\|[^|]*\|[^|]*\|\s*(\w+)\s*\|\s*$", re.MULTILINE)
        return {int(step): tier for step, tier in row.findall(text)}

    def test_guide_table_is_parseable(self):
        table = self.guide_table()
        self.assertTrue(table, "GUIDE section 12 mapping table not found or unparseable")
        self.assertEqual(set(range(1, 22)), set(table),
                         "GUIDE section 12 should map all 21 v14 steps")
        for step, tier in table.items():
            with self.subTest(step=step):
                self.assertIn(tier, TIERS, f"step {step}: unknown tier {tier!r}")

    def test_mapped_steps_exist_in_the_guide(self):
        table = self.guide_table()
        for item in load_json(LIBRARY / "01-phases" / "manifest.json")["items"]:
            step = item.get("v14_step")
            if step is None:
                continue
            with self.subTest(rule=item["id"]):
                self.assertIn(step, table,
                              f"{item['id']}: maps to v14 step {step}, absent from GUIDE §12")

    def test_mapped_tier_agrees_with_the_guide(self):
        table = self.guide_table()
        for item in load_json(LIBRARY / "01-phases" / "manifest.json")["items"]:
            step = item.get("v14_step")
            if step is None or step not in table:
                continue
            with self.subTest(rule=item["id"], step=step):
                self.assertEqual(
                    table[step], item["enforcement_status"],
                    f"{item['id']}: GUIDE §12 calls step {step} '{table[step]}', "
                    f"the rule is '{item['enforcement_status']}'")

    def test_unmapped_rules_say_why(self):
        """A null mapping is fine; an unexplained one is not."""
        for path in phase_rules():
            rule = load_json(path)
            if rule.get("maps_to_v14_step") is not None:
                continue
            with self.subTest(rule=path.stem):
                self.assertTrue(
                    (rule.get("maps_to_v14_step_reason") or "").strip(),
                    f"{path.stem}: maps_to_v14_step is null with no reason given")


# --------------------------------------------------------------------------- #
# Adopter template parity
# --------------------------------------------------------------------------- #
class TemplateParity(unittest.TestCase):
    """``templates/ai-library/`` is what adopters copy; it must not fall behind."""

    def test_file_trees_match(self):
        self.assertTrue(TEMPLATE.is_dir(), f"{TEMPLATE} missing")
        library, template = relative_files(LIBRARY), relative_files(TEMPLATE)
        self.assertEqual(set(), library - template,
                         "in .ai/ but missing from templates/ai-library/")
        self.assertEqual(set(), template - library,
                         "in templates/ai-library/ but missing from .ai/")

    def test_non_exempt_files_are_identical(self):
        for rel in sorted(relative_files(LIBRARY) & relative_files(TEMPLATE)):
            if rel in PARITY_EXEMPT:
                continue
            with self.subTest(file=rel):
                self.assertEqual(
                    (LIBRARY / rel).read_bytes(), (TEMPLATE / rel).read_bytes(),
                    f"{rel}: .ai/ and templates/ai-library/ have diverged")

    def test_exemptions_are_still_needed(self):
        """An exemption that no longer differs is dead weight -- drop it."""
        for rel in sorted(PARITY_EXEMPT):
            with self.subTest(file=rel):
                self.assertTrue((LIBRARY / rel).is_file(), f"{rel}: exempted but absent")
                self.assertNotEqual(
                    (LIBRARY / rel).read_bytes(), (TEMPLATE / rel).read_bytes(),
                    f"{rel}: identical in both trees -- remove it from PARITY_EXEMPT")


# --------------------------------------------------------------------------- #
# Settings wiring
# --------------------------------------------------------------------------- #
class SettingsWiring(unittest.TestCase):
    """Four ``live`` tiers rest on the guard being *registered*, not just written.

    ``resolve_enforcer`` proves ``guard_force_push`` exists in the source. It
    cannot prove Claude Code ever calls it -- that depends on a hook entry in
    ``.claude/settings.json``, a file no other test reads. Delete the entry and
    the guard becomes unreachable code while every tier claim still resolves.
    This class closes that gap.
    """

    def setUp(self):
        self.settings_path = REPO_ROOT / ".claude" / "settings.json"
        self.assertTrue(self.settings_path.is_file(),
                        f"{self.settings_path} missing")
        self.settings = load_json(self.settings_path)

    def _pre_tool_use_entries(self):
        return (self.settings.get("hooks") or {}).get("PreToolUse") or []

    def test_a_pre_tool_use_hook_is_registered(self):
        self.assertTrue(
            self._pre_tool_use_entries(),
            ".claude/settings.json registers no PreToolUse hook, so the Tier-0 "
            "guard never runs -- four artifacts claim `live` on unreachable code")

    def test_the_guard_covers_both_shells(self):
        """A Bash-only matcher is bypassed by the PowerShell tool on Windows."""
        matchers = [e.get("matcher") or "" for e in self._pre_tool_use_entries()]
        for tool in ("Bash", "PowerShell"):
            with self.subTest(tool=tool):
                self.assertTrue(
                    any(tool in m for m in matchers),
                    f"no PreToolUse matcher covers {tool}: {matchers}")

    def test_the_registered_command_is_the_dispatcher(self):
        commands = [
            h.get("command") or ""
            for entry in self._pre_tool_use_entries()
            for h in (entry.get("hooks") or [])
        ]
        self.assertTrue(
            any("workflow_hook.py" in c for c in commands),
            f"PreToolUse is registered but not to the dispatcher: {commands}")

    def test_default_mode_is_plan(self):
        self.assertEqual(
            "plan", (self.settings.get("permissions") or {}).get("defaultMode"),
            "permissions.defaultMode is what makes planning the session default; "
            "rule-task-checklist's enforcement_note describes it")

    def test_artifacts_citing_settings_are_backed_by_this_class(self):
        """Nothing may name settings.json as an enforcer without these checks."""
        for rel, artifact in artifacts():
            refs = [str(r) for r in (artifact.get("enforced_by") or [])]
            if not any(".claude/settings.json" in r for r in refs):
                continue
            with self.subTest(artifact=rel):
                self.assertIn(
                    "tests/test_governance_library.py::SettingsWiring", refs,
                    f"{rel} cites .claude/settings.json but not the test that "
                    "checks it, so the citation is unfalsifiable")


if __name__ == "__main__":
    unittest.main()
