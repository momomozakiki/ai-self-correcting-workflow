# Handover — autonomous golden-rule layer + two defect fixes

**Run date:** 2026-08-05 · **Branch:** `feat/governance-v14-integration`
**Commits:** `66a7e6b` (Part B), plus the Part A commit that follows this file
**State:** 150 tests pass · `--self-test` exit 0, level 5/5 · tree clean, pushed

Read this before the diff. It is the whole record of decisions taken without asking you.

---

## 1. Decisions taken on your behalf

| Decision | Alternative rejected | Why |
|---|---|---|
| `disallowed-tools: AskUserQuestion` in a skill for autonomy | `permissions.defaultMode: "auto"` in `.claude/settings.json` | v2.1.142+ **ignore** `auto` from project settings — *"a repository cannot grant itself auto mode"*. The proposed command also used `>` , which would have **truncated settings.json** and deleted the `PreToolUse` guard registration, silently voiding four `live` tier claims. |
| No third-party research skill | `npx skills add webcpu/deep-research-skill --global` | Not a documented install path (official: `/plugin install <name>@<marketplace>`). Unvetted third party, installed globally, with web access. Docs warn a skill *"can grant itself broad tool access"*. |
| mtime fallback for the Stop flags | Claude Code's `FileChanged` event | `FileChanged` is the *right* mechanism — it watches the disk, so it sees writes from any process. Its matcher is **literal filenames**, and our ledger name rolls over weekly, so a static watch list goes stale in 7 days. On the roadmap if it ever accepts globs. |
| `enforcement_mode` field + a test | A prose note in GUIDE §13 | A claim nothing checks drifts; that is the whole thesis of the governance suite, and it drifted inside one commit last time. |
| Kept the tier vocabulary at three values | Splitting `live` into `live (deny)` / `live (ask)` | Would touch every artifact, both manifests, `GROWTH.md`, both READMEs and the mirror — a large change for what one field and one test capture. |
| Widened `artifacts()` to cover `05-domains/` | Leaving it scoped to `01-phases/` | Otherwise schema, taxonomy, provenance and enforcement-honesty checks would not have applied to the new folder at all. |
| Checklists as **questions**, not prescriptions | *"Use an interface for every service"* | A question makes you look at the code; a prescription tells you what to type and stops being right the moment the codebase differs. |
| `06-components/` left **empty** | Seeding it with blueprints now | A blueprint records a pattern that has already shipped and survived review. Written in advance it is a guess with a filename. `BLUEPRINT_SCHEMA.md` sets the bar instead. |
| **Not** built: the success-metrics table | autonomy rate >80%, blueprint reuse >70%, research quality >90% | Nothing computes any of them. A number nobody measures is the same lie as a tier nobody enforces — the decision record already dropped the ARS/RGC/ACR metrics for this reason. |
| Folded GUIDE's revision history to `GUIDE_CHANGELOG.md` | Leaving it | GUIDE's own v5.0 row instructed the fold "at the next edit" once the table hit 8 rows. Not in the plan; doing it anyway avoided knowingly breaking a documented rule. |

## 2. Assumptions

- **`ask` counts as `live`.** The call cannot proceed without a human, so it produces a
  visible signal. If you think an `ask` should be `convention` instead, the
  `enforcement_mode` field makes that a one-value change per artifact.
- **`git checkout`/`pull` bumping mtimes is acceptable noise.** A pull touching the ledger
  can suppress a real reminder; one touching source can raise a spurious one. Judged rare
  enough for a single-operator repo. Documented in GUIDE §7.3, not hidden.
- **A 2,000-file scan limit is enough** for this repo's `source_directories`. Configurable
  via `stop_hook.mtime_scan_limit`.
- **The OWASP mapping in `rule-security-review` is by category, not verified against a
  current revision.** Said so in its own `provenance.basis`.

## 3. Not verified

- **`ask` behaviour in `dontAsk` mode** — documented, never observed here. The artifacts
  say an `ask` becomes a silent block in that mode; that is read from the docs, not tested.
- **The `handover` skill has no test.** Nothing enforces that it runs or that the file is
  accurate. It is `convention` by the library's own standard; this file is evidence it ran
  once, not that it always will.
- **Your Claude Code version.** Still never supplied. Nothing built here is version-gated,
  and the guard was proven live, so it is no longer blocking — but `disallowed-tools`
  and `context: fork` have version floors I could not check against your install.
- **The three checklists have been trialled once, against one file.** SOLID was exercised;
  the security checklist has not been run against code that handles credentials.

## 4. Awaiting your ratification

Four artifacts I authored that you have not agreed to:

| File | Asserts | Tier |
|---|---|---|
| `.ai/05-domains/rule-solid-review.json` | 5 principles × 2 questions for OO/module code | `convention` |
| `.ai/05-domains/rule-clean-code-review.json` | naming, function shape, duplication, simplicity, comments | `convention` |
| `.ai/05-domains/rule-security-review.json` | secrets, untrusted input, authz, exposure, dependencies | `convention` |
| `.ai/06-components/BLUEPRINT_SCHEMA.md` | the shape and the bar for a blueprint | `convention` |

If ratified, move the decision to `.ai/10-ratification-archive/`. If you reject one,
deleting the file and its manifest entry is enough — `ManifestIntegrity` will catch a
half-removal.

## 5. Manual steps for you

1. **Auto mode, if you want it**, goes in `~/.claude/settings.json` — not this repo:
   `{"permissions": {"defaultMode": "auto"}}`. A repo cannot grant itself auto mode. Note
   this repo currently sets `defaultMode: "plan"` in project settings; a user-level `auto`
   and a project-level `plan` will interact, and I have not tested which wins.
2. **Run `/status`** if you want the version recorded in the decision doc.
3. **Try an autonomous run**: `/autonomous-task <task>`. It will not stop to ask you.

## 6. What broke during this run

- **I used a heredoc four times**, including once to append the ledger — the rule I was
  implementing. The guard escalated correctly each time; approving the prompt is what
  broke it. This is now `docs/RETROSPECTIVE.md`'s newest entry, and it is *why* the
  `enforcement_mode` fix exists rather than being an abstract improvement. One of the four
  was a pointless no-op command I should not have run at all.
- **My own negative-control script had a restore bug** — it rewrote a file via
  `json.dumps` instead of restoring the byte-exact backup, leaving `.ai/` and the template
  mirror diverged. `TemplateParity` caught it immediately, which is the system working;
  restored from the mirror and re-verified green.
- **I predicted the governance suite already covered `05-domains/`. It did not.** The
  `artifacts()` helper was scoped to `01-phases/` and the prohibitions. Found by checking
  rather than assuming, and fixed before the new rules landed.

## 7. Evidence

- Negative controls, Part B: 15 new test methods, **19 failures** before the fix.
- Negative controls, Part A: six deliberate breakages of a domain rule, **all six caught**
  by the check that should catch them, suite green after restore.
- Live proof the Tier-0 guard works (from `7d68087`, still standing): force-push to `main`
  denied via **both** the Bash and PowerShell tools; the same push to this topic branch not
  blocked.
- Ledger: 6 entries added today under `history/2026-W32.md`.
