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

import datetime
import json
import re
import unittest
from pathlib import Path

# The `workflow_hook` import and its `sys.path` insert were removed on 2026-08-29
# with `derive_confidence`, the only symbol this module used from it. An import
# kept "just in case" is how a module grows a dependency nothing needs.

REPO_ROOT = Path(__file__).resolve().parents[1]
LIBRARY = REPO_ROOT / ".ai"
# TEMPLATE (templates/ai-library) removed 2026-08-29 -- the directory is deleted.

TIERS = ("live", "convention", "declarative")

# RISK_BANDS (the CISA five-risk framework and its weight bands) was removed on
# 2026-08-29 with the `RiskTaxonomy` class below. See the note at that site.

# Keys `.ai/GROWTH.md` requires on every rule and prohibition file. `risk_source`
# and `risk_weight` left this list on 2026-08-29 and GROWTH.md in the *next*
# commit, twelve minutes later -- they drifted, and nothing caught it, because
# the test that held the two in step
# (`RiskTaxonomy.test_growth_doc_documents_the_same_taxonomy`) had been removed
# alongside them. The gate auditor caught it. `RetiredMachinery` below now does.
REQUIRED_ARTIFACT_KEYS = (
    "id", "enforcement", "enforcement_status", "provenance",
)

# PARITY_EXEMPT removed 2026-08-29 with `TemplateParity`. It listed the files
# allowed to differ between `.ai/` and its adopter mirror; there is no mirror now.


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def phase_rules():
    return sorted((LIBRARY / "01-phases").glob("rule-*.json"))


def planning_rules():
    return sorted((LIBRARY / "03-planning").glob("rule-*.json"))


def domain_rules():
    return sorted((LIBRARY / "05-domains").glob("rule-*.json"))


def checklist_rules():
    """Every rule carrying a ``checklist`` -- both phases, one list.

    Planning rules review the plan and domain rules review the code, but they
    make identical claims about their items: sourced and phrased as a question.
    Keeping two lists would mean remembering to widen both, and the folder added
    second is the one that gets forgotten.
    """
    return planning_rules() + domain_rules()


def checklist_manifests():
    """(folder name, manifest) for every folder of checklist rules."""
    return [(folder, load_json(LIBRARY / folder / "manifest.json"))
            for folder in ("03-planning", "05-domains")]


def prohibitions():
    return sorted((LIBRARY / "02-market-rules" / "prohibitions").glob("prohibition-*.json"))


def artifacts():
    """Every rule and prohibition file, as (relative path, parsed dict) pairs.

    Checklist rules are included deliberately: a checklist harvested into
    ``03-planning/`` or ``05-domains/`` is an artifact making the same claims as
    a phase rule, so it answers to the same schema, taxonomy and honesty checks.
    Scoping this to ``01-phases/`` would create a folder where half the
    invariants quietly did not apply -- which is how the drift this module
    exists to catch gets in, and did: ``05-domains/`` escaped six invariants
    until this was widened the first time.
    """
    return [(p.relative_to(REPO_ROOT).as_posix(), load_json(p))
            for p in phase_rules() + checklist_rules() + prohibitions()]


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

        .claude/hooks/workflow_hook.py::handle_stop        function must exist
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
# Risk taxonomy -- REMOVED 2026-08-29
# --------------------------------------------------------------------------- #
# `RiskTaxonomy` validated each artifact's `risk_source` against the CISA
# five-risk framework and its `risk_weight` against that source's band, plus a
# cross-check that .ai/GROWTH.md documented the same taxonomy.
#
# Removed with the rest of the per-item metadata machinery in stage 1 of
# plans/golden-rules-migration.md. docs/RETROSPECTIVE.md already recorded that
# the CISA bands do not transfer to a single-operator repository: they are an
# enterprise risk-register vocabulary, and mapping a checklist question onto
# "structural" vs "accountability" was a judgement nobody could make twice the
# same way. A taxonomy applied inconsistently is noise wearing the costume of
# rigour.
#
# The fields remain in the rule files as inert data until stage 3 retires those
# files. Same treatment as `confidence_level`, and for the same reason: editing
# 58 JSON files that are about to be deleted buys nothing.


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


ITEM_ID = re.compile(r"^[A-Z]{2,5}-[A-Z]{3}-\d{2}$")
TASK_SIZES = ("typo_fix", "small_change", "new_module", "major_refactor")
PRIORITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")


def checklist_items():
    """Every (rule path, item) pair across the planning and domain checklists."""
    for path in checklist_rules():
        rule = load_json(path)
        for entry in rule.get("checklist") or []:
            yield path.name, entry


class ChecklistItems(unittest.TestCase):
    """The Golden Rule protocol's claims, held to the code.

    Its central rule is that no item ships without an authoritative source.
    That is checkable, so it is checked -- otherwise "every item is sourced" is
    the same unfalsifiable prose the enforcement tiers used to be. Applying the
    protocol to its own companion document already found a malformed citation
    ("ASVS 5.10", which is two levels of a three-level scheme), so the failure
    mode is real rather than hypothetical.
    """

    def test_domain_rules_exist(self):
        self.assertTrue(list(domain_rules()), "no domain checklists found")

    def test_item_ids_are_well_formed(self):
        for name, entry in checklist_items():
            with self.subTest(rule=name, item=entry.get("id")):
                self.assertRegex(
                    str(entry.get("id", "")), ITEM_ID,
                    "item ids look like SEC-INP-01 so they can be cited in a "
                    "ledger entry or a review")

    def test_item_ids_are_unique_across_the_library(self):
        seen = {}
        for name, entry in checklist_items():
            iid = entry.get("id")
            with self.subTest(item=iid):
                self.assertNotIn(
                    iid, seen,
                    f"{iid} appears in both {seen.get(iid)} and {name}; a cited "
                    "id must resolve to exactly one item")
            seen[iid] = name

    def test_every_item_cites_a_source(self):
        for name, entry in checklist_items():
            with self.subTest(rule=name, item=entry.get("id")):
                self.assertTrue(
                    (entry.get("source") or "").strip(),
                    "the protocol's own rule: an unsourced item does not ship")
                self.assertTrue((entry.get("source_version") or "").strip())

    def test_source_authority_is_on_the_documented_scale(self):
        for name, entry in checklist_items():
            with self.subTest(rule=name, item=entry.get("id")):
                self.assertIn(entry.get("source_authority"), range(1, 11))

    def test_source_consensus_is_a_count(self):
        for name, entry in checklist_items():
            with self.subTest(rule=name, item=entry.get("id")):
                consensus = entry.get("source_consensus")
                self.assertIsInstance(consensus, int)
                self.assertGreaterEqual(consensus, 0)

    # test_confidence_level_recomputes_from_the_items_own_fields was removed on
    # 2026-08-29 with `workflow_hook.derive_confidence`. It checked that each
    # item's stored `confidence_level` matched what its own `source_authority`,
    # `source_consensus` and source age implied. The check was sound; what it
    # guarded was not worth keeping. The `confidence_level` values remain in the
    # rule files as inert data until stage 3 retires those files wholesale.

    def test_every_item_offers_a_remediation_hint(self):
        for name, entry in checklist_items():
            with self.subTest(rule=name, item=entry.get("id")):
                self.assertTrue(
                    (entry.get("remediation_hint") or "").strip(),
                    "a question without a next step is an audit, not a fix")

    def test_questions_are_questions(self):
        """The design rule the whole folder rests on."""
        for name, entry in checklist_items():
            with self.subTest(rule=name, item=entry.get("id")):
                self.assertTrue(
                    str(entry.get("question", "")).rstrip().endswith("?"),
                    "checklists are phrased as questions, never prescriptions")


class ChecklistSelection(unittest.TestCase):
    """Conditional loading is data, defined once, and must stay resolvable.

    "Once" is the load-bearing word. The table lived in
    ``05-domains/manifest.json`` until plan-review checklists arrived and a
    second copy would have been needed; it now sits in
    ``00-system/checklist-selection.json`` and both folders are selected from
    it. :meth:`test_no_folder_manifest_defines_its_own_selection` is what stops
    the second copy coming back.
    """

    SELECTION_PATH = LIBRARY / "00-system" / "checklist-selection.json"

    def setUp(self):
        self.selection = load_json(self.SELECTION_PATH)
        self.manifests = checklist_manifests()

    def _all_items(self):
        for folder, manifest in self.manifests:
            for item in manifest["items"]:
                yield folder, item

    # --- per-rule gating fields -------------------------------------------- #
    def test_task_sizes_come_from_a_closed_vocabulary(self):
        for folder, item in self._all_items():
            with self.subTest(folder=folder, rule=item["id"]):
                self.assertTrue(item.get("task_size_required"))
                for size in item["task_size_required"]:
                    self.assertIn(size, TASK_SIZES)

    def test_priorities_come_from_a_closed_vocabulary(self):
        for folder, item in self._all_items():
            with self.subTest(folder=folder, rule=item["id"]):
                self.assertIn(item.get("priority"), PRIORITIES)

    def test_phases_come_from_a_closed_vocabulary(self):
        declared = set(self.selection["phases"])
        for folder, item in self._all_items():
            with self.subTest(folder=folder, rule=item["id"]):
                self.assertIn(
                    item.get("workflow_phase"), declared,
                    f"{item['id']}: phase {item.get('workflow_phase')!r} is not a "
                    f"phase the selection table knows about {sorted(declared)}")

    def test_manifest_agrees_with_the_rule_files(self):
        """The index is an index, not a second opinion."""
        for folder, item in self._all_items():
            rule = load_json(LIBRARY / folder / item["file"])
            with self.subTest(folder=folder, rule=item["id"]):
                for field in ("category", "priority", "workflow_phase",
                              "task_size_required", "tech_stack_required"):
                    self.assertEqual(rule.get(field), item.get(field),
                                     f"{item['id']}: manifest and rule disagree "
                                     f"on {field}")
                self.assertEqual(len(rule.get("checklist") or []), item.get("items"))

    # --- the single selection table ---------------------------------------- #
    def test_no_folder_manifest_defines_its_own_selection(self):
        """One table, or the two will answer differently and both look right."""
        for folder, manifest in self.manifests:
            with self.subTest(folder=folder):
                self.assertNotIn(
                    "selection", manifest,
                    f"{folder}/manifest.json carries its own selection block -- "
                    f"the one table is {self.SELECTION_PATH.name}")

    def test_each_phase_points_at_the_folder_that_holds_it(self):
        for phase, block in self.selection["phases"].items():
            with self.subTest(phase=phase):
                self.assertTrue(
                    (LIBRARY / block["folder"]).is_dir(),
                    f"phase {phase} names folder {block['folder']}, which does not exist")

    def test_phase_categories_match_the_rules_on_disk(self):
        """Both directions: no phantom category, no unreachable rule.

        A category in the table with no rule file selects nothing; a rule whose
        category the table omits can never be selected. Either way the rule does
        not run, and only one of the two is visible by reading the folder.
        """
        for phase, block in self.selection["phases"].items():
            folder = block["folder"]
            manifest = load_json(LIBRARY / folder / "manifest.json")
            on_disk = {i["category"] for i in manifest["items"]}
            declared = set(block["categories"])
            with self.subTest(phase=phase, direction="table -> disk"):
                self.assertEqual(set(), declared - on_disk,
                                 f"phase {phase} lists categories with no rule file")
            with self.subTest(phase=phase, direction="disk -> table"):
                self.assertEqual(set(), on_disk - declared,
                                 f"{folder} holds categories the table cannot select")

    def test_every_context_maps_to_categories_that_exist(self):
        categories = {item["category"] for _, item in self._all_items()}
        for context, wanted in self.selection["contexts"].items():
            with self.subTest(context=context):
                self.assertEqual(
                    set(), set(wanted) - categories,
                    f"{context} selects categories with no rule file")

    def test_every_phase_two_category_is_reachable_from_some_context(self):
        """A checklist nothing can select is a checklist nothing will run.

        Phase 1 is exempt by design: its rules are selected by phase alone, so
        `contexts` -- which narrows by what the code touches -- has nothing to
        say about a plan that has not decided what it touches yet.
        """
        selectable = {c for wanted in self.selection["contexts"].values() for c in wanted}
        phase_two = set(self.selection["phases"]["2"]["categories"])
        self.assertEqual(set(), phase_two - selectable,
                         "these categories are unreachable by any task context")

    def test_planning_rules_are_never_gated_on_tech_stack(self):
        """A plan's problem statement is no better or worse for being written in Go.

        A stack filter at Phase 1 could only ever exclude a question that still
        applied, and would do it silently.
        """
        for path in planning_rules():
            rule = load_json(path)
            with self.subTest(rule=path.stem):
                self.assertEqual(
                    [], rule.get("tech_stack_required"),
                    f"{path.stem}: gates on tech stack, but it reviews a plan")


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
# Adopter template parity -- REMOVED 2026-08-29
# --------------------------------------------------------------------------- #
# `TemplateParity` guarded `templates/ai-library/`, the adopter copy of the
# governance library. That directory was deleted in stage 1 of the golden-rules
# migration (`plans/golden-rules-migration.md`), so these three tests guarded
# nothing and errored on a missing path.
#
# Deleting a test is normally how coverage disappears silently, so the reason is
# recorded rather than assumed: the mirror was *distribution* machinery -- a
# second copy of 58 files kept byte-identical so adopters could vendor them. The
# rules themselves are untouched and still tested by every other class here.
# What went away is the obligation to maintain a duplicate, not any check on
# content.
#
# The parity *principle* survives where it still has a subject:
# `test_claude_layout.TemplateMirrors` covers `.claude/rules/` and
# `.claude/agents/`, and `test_skills.SkillTemplateParity` covers
# `templates/skills/`. Both gained non-empty-corpus guards in the same commit,
# because two empty trees compare equal and pass.


# --------------------------------------------------------------------------- #
# Settings wiring
# --------------------------------------------------------------------------- #
class SettingsWiring(unittest.TestCase):
    """Four ``live`` tiers rest on the guard being *registered*, not just written.

    ``resolve_enforcer`` proves ``guard_force_push`` exists in the source. It
    cannot prove Claude Code ever calls it -- that depends on a hook entry in a
    settings file. Delete the entry and the guard becomes unreachable code while
    every tier claim still resolves. This class closes that gap.

    It checks **both** configs, because for most of this repository's life it
    checked only ``.claude/settings.json`` -- and
    ``templates/settings.json.hooks``, the fragment adopters actually merge,
    had no ``PreToolUse`` block at all. Every adopter ran with the four Tier-0
    prohibitions documented as ``live`` and nothing enforcing them, and the
    suite was green throughout. A test that reads only the copy its own
    repository uses cannot see what ships.
    """

    # (label, path, substring the dispatcher command must contain). The paths
    # differ because an adopter reaches the dispatcher through the submodule.
    CONFIGS = (
        ("repo", REPO_ROOT / ".claude" / "settings.json",
         ".claude/hooks/workflow_hook.py"),
        ("adopter template", REPO_ROOT / "templates" / "settings.json.hooks",
         ".claude/workflow-core/.claude/hooks/workflow_hook.py"),
    )

    def configs(self):
        for label, path, command in self.CONFIGS:
            self.assertTrue(path.is_file(), f"{path} missing")
            yield label, load_json(path), command

    @staticmethod
    def _pre_tool_use_entries(settings):
        return (settings.get("hooks") or {}).get("PreToolUse") or []

    def test_a_pre_tool_use_hook_is_registered(self):
        for label, settings, _ in self.configs():
            with self.subTest(config=label):
                self.assertTrue(
                    self._pre_tool_use_entries(settings),
                    f"{label} registers no PreToolUse hook, so the Tier-0 guard "
                    "never runs -- four artifacts claim `live` on unreachable code")

    def test_the_guard_covers_both_shells(self):
        """A Bash-only matcher is bypassed by the PowerShell tool on Windows."""
        for label, settings, _ in self.configs():
            matchers = [e.get("matcher") or ""
                        for e in self._pre_tool_use_entries(settings)]
            for tool in ("Bash", "PowerShell"):
                with self.subTest(config=label, tool=tool):
                    self.assertTrue(
                        any(tool in m for m in matchers),
                        f"{label}: no PreToolUse matcher covers {tool}: {matchers}")

    def test_the_registered_command_is_the_dispatcher(self):
        """The path differs per config, so matching on the filename is not enough."""
        for label, settings, expected in self.configs():
            commands = [
                h.get("command") or ""
                for entry in self._pre_tool_use_entries(settings)
                for h in (entry.get("hooks") or [])
            ]
            with self.subTest(config=label):
                self.assertTrue(
                    any(expected in c for c in commands),
                    f"{label}: PreToolUse is registered but not to {expected!r}: "
                    f"{commands}")

    def test_default_mode_is_plan(self):
        for label, settings, _ in self.configs():
            with self.subTest(config=label):
                self.assertEqual(
                    "plan", (settings.get("permissions") or {}).get("defaultMode"),
                    f"{label}: permissions.defaultMode is what makes planning the "
                    "session default; rule-task-checklist's enforcement_note "
                    "describes it")

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


# --------------------------------------------------------------------------- #
# Retired machinery
# --------------------------------------------------------------------------- #
class RetiredMachinery(unittest.TestCase):
    """Deleted machinery must not still be described as if it runs.

    This exists because the failure it guards happened **three times in one
    session**, each time in the commit closing a report of the previous one:

    1. `templates/ai-library/` and `TemplateParity` were deleted, and
       `.claude/rules/governance-library.md` -- unconditional, loaded every
       session -- went on instructing the next session to mirror into that
       directory.
    2. Fixed, and `GUIDE.md` was left asserting that this module holds
       `risk_source`/`risk_weight` to the CISA taxonomy and `.ai/` to its mirror.
       Both classes were gone.
    3. Fixed, and `.ai/GROWTH.md` was left telling rule authors their
       `confidence_level` would be derived by `derive_confidence`.

    **The first version of this class caught none of them**, and the gate auditor
    proved it by reintroducing all three into a green suite. That version
    allowlisted whole *files*, so it detected only a retired name surfacing
    somewhere new -- while every incident was a false claim inside a file that
    legitimately discusses the removal. Allowlisting the file that gets it wrong
    is exactly the wrong granularity.

    So the unit here is the **paragraph**, and the question is not "may this file
    mention the name" but "does this passage admit the thing is gone". A
    paragraph naming retired machinery must also carry a removal marker
    (`removed`, `deleted`, `no longer`, `was`, `used to`, ...). That is crude and
    deliberately so: it cannot judge whether prose is *correct*, only whether it
    is written as history. A sentence claiming deleted code enforces something,
    with no acknowledgement that it is gone, fails.

    Records of what used to be true are exempt wholesale -- a changelog, a
    ledger, an archive. They are supposed to say what was.

    **What this does not catch, stated plainly.** The marker is paragraph-scoped
    and blind to what the marker is *about*. A paragraph that says "v1.0 called
    this live while nothing checked it" and then asserts a deleted class enforces
    something today contains both a past-tense phrase and a false claim, and
    passes. That exact case existed in
    ``docs/governance-integration-decision.md`` and had to be found by hand.
    So this is a floor, not a proof: it catches the careless restatement, not
    the well-written falsehood. Do not read a green run as "no stale claims".
    """

    #: Symbols and paths deleted in the golden-rules migration. Add a name here
    #: the moment you delete the thing, not afterwards.
    #:
    #: Matched on word boundaries, so `TemplateParity` does not fire inside
    #: `SkillTemplateParity` -- a live class whose name happens to contain a
    #: retired one. Substring matching produced exactly that false positive and
    #: would have trained the next reader to widen the allowlist.
    RETIRED = (
        "derive_confidence", "CONFIDENCE_MATRIX", "RiskTaxonomy", "RISK_BANDS",
        "TemplateParity", "maturity-tracker", "maturity_tracker",
        "maturity level", "templates/ai-library", "risk_weight", "risk_source",
    )

    #: Retired *fields* rather than retired *code*. In a `.json`/`.yaml` file
    #: these are data keys sitting inertly in rule files that stage 3 deletes
    #: wholesale -- not a claim that anything enforces them. In prose they are a
    #: claim, and still checked. Without this split the test demands the removal
    #: of 58 files' data, which is the churn stage 1 deliberately deferred.
    DATA_KEYS = frozenset({"risk_source", "risk_weight"})
    DATA_SUFFIXES = (".json", ".yaml", ".yml")

    @classmethod
    def names_in(cls, block, suffix=""):
        """Retired names appearing in ``block`` as whole words."""
        candidates = [n for n in cls.RETIRED
                      if not (suffix in cls.DATA_SUFFIXES and n in cls.DATA_KEYS)]
        return [n for n in candidates
                if re.search(rf"(?<![\w-]){re.escape(n)}(?![\w-])", block)]

    #: A paragraph naming retired machinery must contain one of these. They are
    #: past-tense or negating: prose carrying one is discussing a removal, prose
    #: carrying none is describing live behaviour.
    MARKERS = re.compile(
        r"\bremov|\bdelet|\bno longer|\bwas\b|\bwere\b|\buntil\b|\bformerly\b|"
        r"\bused to\b|\bretir|\bgone\b|\bdropp|\bobsolet|\bdeprecat|"
        r"\bnot required|\binert\b|\bsuperseded\b|~~",
        re.IGNORECASE)

    #: Records of a prior state. Exempt by nature, not by exception.
    ALWAYS_SKIPPED = (
        "plans/archive/", "history/", "docs/self-growing-checklist-ecosystem/",
        "CHANGELOG.md", "GUIDE_CHANGELOG.md", "plans/HANDOVER.md",
    )
    #: This module names every retired symbol in RETIRED above, so it matches by
    #: construction and cannot check itself.
    SELF = "tests/test_governance_library.py"

    SKIPPED_DIRS = {".git", "__pycache__", "node_modules"}
    #: By extension *and* by exact name -- the adopter fragment and the settings
    #: fragment carry suffixes no ordinary glob would catch, and
    #: `templates/CLAUDE.md.fragment` is named in the migration plan as a
    #: stage-3 silent-breakage site.
    #: Binary and generated files, skipped by extension. Everything *else* that
    #: git tracks is scanned. This is a **skip-list, not an allow-list**: the
    #: gate auditor defeated the allow-list version on 2026-08-29 by putting a
    #: live `TemplateParity` instruction in `docs/MIRRORING.mdx` -- `.mdx` was
    #: simply not in the list, so the file was never opened. An allow-list of
    #: extensions fails silently for every extension nobody thought of, which is
    #: the exact shape of the defect this class exists to catch.
    SKIPPED_SUFFIXES = (
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".pdf",
        ".zip", ".gz", ".tar", ".whl", ".pyc", ".exe", ".dll", ".so",
        ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3",
    )

    def scanned_files(self):
        for path in sorted(REPO_ROOT.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            if set(path.relative_to(REPO_ROOT).parts) & self.SKIPPED_DIRS:
                continue
            if rel.startswith(self.ALWAYS_SKIPPED) or rel in self.ALWAYS_SKIPPED:
                continue
            if rel == self.SELF:
                continue
            if path.suffix.lower() in self.SKIPPED_SUFFIXES:
                continue
            yield rel, path

    @staticmethod
    def paragraphs(text):
        """Blank-line separated blocks, with their 1-based starting line."""
        block, start = [], 1
        for number, line in enumerate(text.splitlines(), start=1):
            if line.strip():
                if not block:
                    start = number
                block.append(line)
            elif block:
                yield start, "\n".join(block)
                block = []
        if block:
            yield start, "\n".join(block)

    def offenders(self):
        for rel, path in self.scanned_files():
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for start, block in self.paragraphs(text):
                named = self.names_in(block, path.suffix)
                if named and not self.MARKERS.search(block):
                    yield rel, start, named, block

    def test_the_corpus_is_not_empty(self):
        files = list(self.scanned_files())
        self.assertGreater(len(files), 50,
                           f"only {len(files)} files scanned -- this check is "
                           "passing vacuously")

    def test_no_paragraph_describes_retired_machinery_as_live(self):
        found = list(self.offenders())
        report = "\n\n".join(
            f"{rel}:{start} names {named} with no acknowledgement it is gone:\n"
            "    " + block.strip().replace("\n", "\n    ")[:400]
            for rel, start, named, block in found)
        self.assertEqual(
            [], [f"{rel}:{start}" for rel, start, _, _ in found],
            "These passages describe deleted machinery as though it still runs. "
            "Rewrite them as history, or say plainly that it was removed:\n\n"
            + report)

    def test_the_marker_check_actually_fires(self):
        """A guard that has never failed is not a guard.

        The first version of this class passed against all three incidents it
        was written for. This runs one of them through the real detector rather
        than trusting that the logic reads correctly.
        """
        incident = ("`confidence_level` is then **derived** by "
                    "`.claude/hooks/workflow_hook.py::derive_confidence`; "
                    "never type one by hand.")
        blocks = list(self.paragraphs(incident))
        self.assertEqual(1, len(blocks))
        _, block = blocks[0]
        self.assertTrue(self.names_in(block),
                        "the detector no longer recognises a retired name")
        self.assertIsNone(self.MARKERS.search(block),
                          "this incident text must read as a live claim")

        excused = incident + " This was deleted on 2026-08-29."
        self.assertIsNotNone(self.MARKERS.search(excused),
                             "an explicit removal note must clear the check")



if __name__ == "__main__":
    unittest.main()
