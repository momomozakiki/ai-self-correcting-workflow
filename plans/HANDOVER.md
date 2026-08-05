# Handover — adopting both staging documents

**Run date:** 2026-08-05 · **Branch:** `feat/governance-v14-integration`
**State:** 184 tests pass · `--self-test` **5/5 on its own merits** · `docs/to-be-implement/` gone

Read this before the diff. It is the whole record of decisions taken without asking you.

---

## 1. Items dropped for want of a source

The protocol's rule is that an unsourced item does not ship. **The source documents
sketched ~200 items; 80 shipped.** The shortfall is the rule working, not an omission.

| Dropped | What was sought | Why it did not resolve |
|---|---|---|
| *"SCA scanning integrated into CI"* | A standard mandating a specific scanner | OWASP documents the *practice*, not a tool. Naming Dependency-Check would be a prescription, which the checklist design forbids. Kept as the sourced question "are components within your remediation window?" (ASVS V15.2.1). |
| Kubernetes admission-control and DaemonSet items | NIST SP 800-190 language supporting them | 800-190 predates most of it. Citing it would repeat the overstatement I corrected in the originals. |
| *"Can a new developer understand the architecture within one week?"* | Any authority for the one-week figure | The number is folklore. Kept the question, dropped the interval. |
| Numeric thresholds generally — function length, coverage %, complexity scores | A standard fixing the number | None fixes one. A "20-line limit" produces 19-line incoherent functions. Kept as judgement questions. |
| ~120 further items across all ten categories | — | Either restated an item already present, or I could not resolve a citation at authority ≥ 5 within this task. |

## 2. `task_size` classification — please confirm

**I classified this run as `major_refactor`.** Reason: it changed hook behaviour across
three call sites, added a new library folder with ten artifacts, and restructured
documentation. Under that classification the loading table selects architecture,
code-quality, security, testing, error-handling, performance and audit.

This is a judgement made before the work existed, and nothing downstream can validate it.
If you think this was `new_module`, the difference is that the architecture and audit
checklists would not have loaded.

## 3. `source_consensus` counts — please verify

Every item stores a consensus count: independent sources at authority ≥ 7 supporting it.
**The tests enforce that the field is present and numeric. They do not and cannot check
that the count is right** — that is a human gate, and saying so plainly is the point.

The counts I assigned are conservative (mostly 2–4). The ones most worth challenging are
where I claimed 4: `SEC-INP-02` (query parameterization) and `SEC-AUT-02` (object-level
authorization). Both are near-universally mandated, but "4 independent sources" is my
estimate, not a tally I can show you.

## 4. Decisions taken on your behalf

| Decision | Rejected alternative | Why |
|---|---|---|
| Confidence **derived** by `derive_confidence` | Storing an asserted level | A number nobody recomputes drifts. `CONFIDENCE_MATRIX` is a threshold ladder, not a lookup, so `(10, 4, 6)` correctly yields 5. |
| Confidence **percentages dropped** | Modelling 95–100% etc. | No procedure separates 94% from 96%. |
| **No ±2 self-adjustment** | The documents' performance loop | The agent that applied a rule would decide its own false-positive rate, then feed that grade into whether the rule is trusted. No ground truth in the loop. |
| Metrics to `08-behavioral-metrics/`, never into rule files | `performance_history` per rule | Mutable rule files would put `.ai/` and `templates/` permanently out of sync, failing `TemplateParity` every run. |
| Timer-based revalidation (180d) | Source-version detection | A hand-maintained version manifest goes stale silently — the failure already in `RETROSPECTIVE.md`. |
| SOLID + clean-code **folded** into architecture and code-quality | Keeping them as separate rules | They were the same items under different headings; two homes for one question is drift. |
| `git status --porcelain -uall` | Plain porcelain | Git collapses a wholly untracked `plans/` to one entry, hiding the breadcrumb inside it. Found by a test, not by reading. |
| Widened `artifacts()` to cover `05-domains/` | Leaving it scoped | Otherwise schema, taxonomy and provenance checks would not apply to the new folder at all. |
| Probe script, not a `--probe-filechanged` flag | The flag the plan specified | Permanent hook surface for a one-off question — the objection already used against `--no-write` and `--verify-sources`. |

## 5. Assumptions

- **Age in the confidence derivation is measured from when the *guidance* was established**,
  not when the item was written. HTTP semantics date from 1997 even though RFC 9110 is 2022.
- **Authority tiers** are my reading of the protocol's table: OWASP/NIST at 9, RFCs/ISO at
  10, industry books at 5.
- **`revalidation_interval_days: 180`** is the documents' suggestion, not a sourced figure.

## 6. Not verified

- **The `FileChanged` probe was inconclusive, not negative.** A matcher-less entry logged
  nothing, but hook registration may need a session restart, the event needs v2.1.146+ and
  this environment cannot report its CLI version, and an empty matcher may mean "watch
  nothing". Recorded as inconclusive in the decision record §10.
- **Tech-stack gating is per *rule*, not per *item*.** The database checklist covers SQL and
  NoSQL together, so a Mongo project loads it whole. The meaningful case — no database in
  the stack at all — correctly loads nothing.
- **The ten checklists have not been run against real code**, unlike the SOLID trial in the
  previous commit. The loading table was trialled; the items themselves have not been.
- **Your Claude Code version**, still never supplied.

## 7. Awaiting your ratification

Ten new `convention` artifacts in `.ai/05-domains/` plus `docs/checklist-system.md`. I
authored them; you have not agreed to them. Ratified items move to
`.ai/10-ratification-archive/`.

## 8. What broke during this run

- **I predicted `artifacts()` already covered `05-domains/`. It did not** — six invariants
  would have silently skipped the new folder. Found by checking, then verified by breaking
  a domain rule ten ways; all ten caught.
- **The first generator run omitted `source_established`**, making `confidence_level`
  unverifiable — an asserted number again, inside the change built to stop that. The test
  caught it with 80 failures before anything shipped.
- **My own restore logic re-dumped JSON instead of restoring bytes** in an earlier control
  script, diverging `.ai/` from the mirror. Fixed by restoring from the backup file
  byte-exact; this run's control script does that.
- **The GUIDE revision table exceeded three rows** and the decision-record rows landed out
  of order. Both corrected.

## 9. Evidence

| Check | Result |
|---|---|
| Part 1 negative control | **23 failures** across 19 new methods before the fix |
| Checklist negative control | **80 failures** — one per item — before `source_established` existed |
| Deliberate breakage | **10 of 10 caught** by the check that should catch each |
| Two-Stop cascade | breadcrumb written on Stop 1; Stop 2 **did not** re-fire; human plan preserved and still reported |
| Loading trial | typo fix 9 items · new API 34 · no-database project loads no database rule |
| Suite | 184 pass (34 new) |
| `--self-test` | 5/5, `docs_have_frontmatter` true because the docs are real — not suppressed |
