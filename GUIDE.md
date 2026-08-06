---
title: Adaptive Self-Correcting Workflow for AI Coding Agents
version: 5.4
last_validated: 2026-08-05
official: true
source: agent-generated
tags: [workflow, governance, reference, hooks, provenance, runtime]
applies_when: "Understanding, adopting, or modifying the Adaptive Self-Correcting Workflow itself."
estimated_tokens: 8200
---

# Adaptive Self‑Correcting Workflow for AI Coding Agents  
*Version 5.4 – Centralized, Configurable, Self‑Improving, Governed*

**Central Workflow Repository:** `ai-self-correcting-workflow` (this repository)

## Revision History
Latest three only — the full history lives in [`GUIDE_CHANGELOG.md`](GUIDE_CHANGELOG.md),
folded there per §6.3 when this table passed ~8 rows.

| Version | Date       | Change                                                                                     |
|---------|------------|--------------------------------------------------------------------------------------------|
| 5.4     | 2026-08-05 | §13: **plan review.** `05-domains/` reviews code against the plan and so cannot see a defect in the plan; `03-planning/` adds 5 sourced categories, 31 items, answered at Phase 1. The selection table moves to `.ai/00-system/checklist-selection.json` and gains a `workflow_phase` axis, so one table serves both folders. |
| 5.3     | 2026-08-05 | §13: the checklist system lands — ten sourced categories in `05-domains/`, `confidence_level` derived rather than asserted, and conditional loading defined once as manifest data. §7.3/§7.4: the Stop hook stops counting its own breadcrumb as work, and `--self-test` now reports which gate blocked the maturity climb rather than only the floor. New [`docs/checklist-system.md`](docs/checklist-system.md). |
| 5.2     | 2026-08-05 | §7.3: the Stop flags gain a modification-time fallback, because `PostToolUse` sees only the editing tools and both failure directions showed up in practice. §13: `live` now distinguishes `deny` from `ask` strength via a tested `enforcement_mode`, after an `ask` was waved through and the rule it guarded was broken anyway. |

---

## 1. Philosophy & Overview

**What**  
A disciplined meta‑framework for AI‑assisted development that combines fixed safety invariants, per‑task dynamic planning, conditional documentation updates, filesystem‑native memory, and a closed‑loop improvement cycle. Every project using this workflow pulls its core automation from a single, versioned **workflow repository**, and every project contributes improvements back.

**Why**  
Multi‑session AI development fails when documentation drifts, handoff is broken, changes are untraceable, and external information is trusted blindly. Without a single source of truth for the *process itself*, each project re‑invents discipline or, worse, abandons it. Centralizing the workflow while allowing per‑project configuration solves both the coherence and the adaptation problem.

**How – The Philosophy**  
“Fixed invariants for safety; dynamic planning for agility; hooks for ambient awareness; history for accountability; provenance for trust; one workflow to rule them all.”

- **Fixed invariants** are mandatory and encoded in a shared `CLAUDE.md` fragment that every project includes.
- **Dynamic planning** lets the agent design a task‑specific checklist, now including the obligation to log every intentional change and verify sources.
- **Conditional updates** ensure we document only when something matters; the history ledger captures **significant** changes (not noise), preserving traceability without fatigue.
- **Hooks** inject context and reminders; all hook logic lives in the central repository, driven by project‑local configuration.
- **Self‑improvement**: any project that discovers a flaw or missing trigger contributes a patch upstream; after merge, every other project inherits the improvement on its next update.

---

## 2. Repository Structure

### 2.1 The Central Workflow Repository (`workflow-core`)

```
workflow-core/
├── README.md                     # Quick start, philosophy, link to full guide
├── GUIDE.md                      # This document (the full workflow reference)
├── CHANGELOG.md                  # Semantic versioning of workflow changes
├── ROADMAP.md                    # Planned improvements to the workflow itself
├── .ai/                          # Governance library (§13) — this repo's own instance
├── docs/
│   ├── RETROSPECTIVE.md          # Mistakes → rules (the self-hardening loop)
│   ├── governance-integration-decision.md   # Which controls are enforced, and why
│   ├── claude-code-hook-integration/        # Hook integration guide (folded)
│   └── self-growing-checklist-ecosystem/    # Imported v14 reference (folded)
├── history/                      # The workflow’s own ledger (practice what you preach)
│   ├── FORMAT.md
│   └── YYYY-Www.md
├── hooks/
│   └── workflow_hook.py          # Generic dispatcher, reads project config
├── .claude/skills/               # The only path Claude Code discovers skills at
│   ├── adaptive-workflow/        # Agent process manual (SKILL.md + references/)
│   ├── autonomous-task/          # Unattended runs (removes AskUserQuestion)
│   ├── handover/                 # The review checklist an unattended run leaves
│   └── skill-authoring/          # How to structure, size and split a skill
├── schemas/
│   ├── hook_contract.md          # Validated I/O shapes + --self-test contract
│   └── config_schema.json        # Schema for project workflow_config.json
├── templates/
│   ├── CLAUDE.md.fragment        # Blocks to include in a project’s CLAUDE.md
│   ├── settings.json.hooks       # Hook definitions for .claude/settings.json
│   ├── workflow_config.json      # Default configuration (to be customized)
│   ├── skills/                   # Mirror of .claude/skills/ — adopters copy this
│   └── ai-library/               # Governance library scaffold for adopters
├── tests/
│   ├── test_hook.py              # Synthetic event tests for the hook dispatcher
│   ├── test_governance_library.py  # Integrity of the .ai/ library
│   └── test_skills.py            # Skill structure, size, location and parity
└── CONTRIBUTING.md               # How to propose improvements
```

### 2.2 A Project’s Structure After Adoption

```
my-project/
├── CLAUDE.md                     # Includes workflow fragment + project custom bits
├── .claude/
│   ├── workflow-core/            # Git submodule pointing to central repo
│   │   └── (contents above)
│   ├── skills/                   # Copied from workflow-core/templates/skills/ —
│   │   └── adaptive-workflow/    #   Claude Code discovers skills only here
│   ├── settings.json             # Merged with templates/settings.json.hooks
│   └── workflow_config.json      # Project-specific paths/feature flags
├── .ai/                          # Living docs (if used)
├── docs/
├── history/
├── plans/
├── ROADMAP.md
├── src/
├── tests/
└── ...
```

The `workflow_config.json` maps generic concepts to project paths and enables/disables features. Example:

```json
{
  "project_root": ".",
  "roadmap_file": "ROADMAP.md",
  "retrospective_file": "docs/RETROSPECTIVE.md",
  "ledger": {
    "enabled": true,
    "directory": "history"
  },
  "source_directories": ["src", "lib"],
  "documentation_directories": ["docs", ".ai"],
  "env_check": {
    "tool_paths": {
      "dart": {
        "path": "C:\\Users\\ST-Service\\.puro\\envs\\default\\flutter\\bin\\dart.bat",
        "version_flag": "--version"
      },
      "some-tool-no-version-flag": {
        "path": "/usr/local/bin/sometool",
        "version_flag": null
      }
    }
  },
  "stop_hook": {
    "max_blocks": 2
  }
}
```

If `version_flag` is omitted, `--version` is used. If set to `null` (or an empty string), the hook will only verify that the file exists at the given path, without attempting to query its version. Paths are relative to the project root unless absolute.

---

## 3. Core Concepts

### 3.1 Fixed Invariants
Safety‑net steps that always run at session start: pull latest code, check environment, load living documents, surface any unfinished plan. They are enforced by the `SessionStart` hook and echoed in `CLAUDE.md`.

### 3.2 Dynamic Planning
The agent creates a **task‑specific checklist** after understanding the user’s request. This merges the invariants with domain‑specific steps, ledger entries, provenance checks, and documentation updates.

### 3.3 Change‑History Ledger
A weekly chronological record of every **intentional** change (not every keystroke). Stored under `history/YYYY-Www.md`. The hook reminds the agent to write an entry before committing, and the closure phase enforces it.

### 3.4 Documentation Standard
Every document (external or agent‑generated) carries a single **YAML frontmatter block** stating its origin, official status, version, and validation date, plus a visible **Revision History** table. This prevents blind trust in unverified information and keeps version history readable. Large documents are split per the Progressive Disclosure Guide. See §6 for the full specification.

### 3.5 Hooks
A single Python dispatcher (`workflow_hook.py`) is triggered by `SessionStart`, `PostToolUse`, and `Stop` events. It maintains per‑session state to provide ambient reminders without being intrusive.

---

## 4. Workflow Phases

Each phase is presented as a checklist for the AI agent to follow.  
Items marked with `[ ]` are actionable steps; the agent should tick them off mentally or in a plan document.

### Phase 0 – Fixed Invariants (Always do first)

> **Tier 0 — absolute prohibitions.** Never force-push a shared branch, never
> commit secrets, never rewrite published history, never delete the ledger or plan
> archive. These are not overrideable by config or by instruction. Full set:
> `.ai/02-market-rules/prohibitions/`.

- [ ] **F1 – Git sync**  
  `git fetch && git pull --rebase`.  
  Check for a dirty working tree; if dirty, ask user how to handle (continue, stash, commit, etc.).

- [ ] **F2 – Environment check**  
  Read the `env_check.tool_paths` from the project’s `workflow_config.json`. For each tool listed:
  - If `version_flag` is a non‑empty string, run `<path> <version_flag>` to get version.
  - If `version_flag` is `null` or empty, only verify that the path exists (without attempting a version command).
  Report versions or “found”/“not found” accordingly. If the config is empty, skip.

- [ ] **F3 – Load & verify living documents**  
  Read all living documents defined in config (e.g., `.ai/best_practices.md`, `docs/architecture.md`).  
  For **every** loaded documentation file, check for the doc frontmatter (provenance + version fields per §6), or a sidecar `.prov.md` for non‑commentable formats.  
  - If missing, flag the file: *“Document [file] has no frontmatter (provenance/version). Is it from an official source? I will add the block once confirmed.”*  
  - Do **not** block the session; just note for later.

- [ ] **F4 – Unfinished plan & Roadmap**  
  If `plans/UNFINISHED.md` exists, **immediately** surface it to the user:  
  *“⚠️ Unfinished plan detected: [summary]. Should we continue it or archive it?”*  
  If the configured roadmap file exists, note the next unchecked item from the first active epic (stop at `## Completed Epics` / `## Backlog`).

- [ ] **F5 – Daily workflow update check** (once per day)  
  This ensures the central workflow submodule stays up‑to‑date.  
  - If `.claude/workflow-core` submodule does **not** exist, note that the workflow is not yet linked; skip the check. The `.ai/.workflow_check_date` file should only be created after the submodule is present to avoid permanent “no submodule” warnings.
  - Otherwise, read the last check date from `.ai/.workflow_check_date`. If today’s date ≠ stored date:
    - `cd .claude/workflow-core && git fetch origin`
    - Compare local and remote (`git rev-list --count HEAD..origin/main`).
    - If new commits exist, inject context: *“🔄 Workflow updates available (X new commits). Review and update? I can run `git submodule update --remote` and apply changes.”*
    - Update `.ai/.workflow_check_date` with today’s date.
    - If user approves, update submodule and validate that any new mandatory steps (new triggers, invariants) are absorbed.

### Phase 1 – Meta‑Planning (Design the Task‑Specific Checklist)

- [ ] Assess the user’s request:
  - Task scope (trivial fix, feature, refactor, architecture change).
  - Documentation impact (will it change living docs?).
  - Multi‑session handoff needed? → plan uses `UNFINISHED.md`.
  - Validation rigor (linter, unit tests, full suite).
  - Retrospective value (mistake, new gotcha).
  - **Provenance requirement:** does the task involve external documents? If yes, plan a step to verify source and add `SOURCE‑PROVENANCE`.
  - **History ledger:** all intentional changes will be logged; plan includes ledger update steps.

- [ ] **Chunk large tasks** using the roadmap:
  - If the request is part of an epic, consult the roadmap.
  - Select the next logical, unblocked task as the current `UNFINISHED.md` item.

- [ ] **Produce a concrete bullet checklist** (with acceptance criteria) for this specific task.  
  The checklist must include **only** the necessary process steps (linter, tests, doc update, ledger entry, provenance, retro, archive).  
  *Optionally present the plan to user for confirmation.*

### Phase 2 – Execute the Dynamic Plan

For each bullet in the task‑specific plan, **implement, validate, and apply conditional triggers**:

#### Implementation & Validation
- [ ] Write code / docs / design as planned.
- [ ] Immediately run linter, formatter, and relevant tests. Fix failures before moving on.
- [ ] **Verify reversibility before destructive work.** Git is the rollback
  mechanism: make sure a clean commit checkpoint exists before anything hard to
  undo. If an operation can't be reversed, say so *before* running it.
- [ ] **Watch for loops.** If the same call repeats with identical arguments and
  no progress, change the approach rather than retrying — vary the arguments,
  read the error, or ask. The `PostToolUse` hook flags this at 3 consecutive
  identical calls (§7.3), but noticing first is cheaper than being told.
- [ ] **Never feed a program or message over heredoc stdin.** Write the script to
  a file and run the file; use the editing tools for source changes. Shell and
  tool layers mangle escape sequences, and the corruption is silent until a
  pattern misses. Same root cause as the `git commit -F -` caveat in Phase 3.
- [ ] If an obstacle arises, **log it**, propose an updated plan, await user approval, then continue.

#### Conditional Update Triggers (apply **during and after** each change)

| Trigger | Action |
|---------|--------|
| **New pattern / rule / gotcha** | Append to `.ai/best_practices.md` (with example). |
| **New naming convention** | Append to `.ai/naming_conventions.md`. |
| **Change to public API, architecture, or data flow** | Update corresponding `docs/*.md` with dated annotation. |
| **Document created or updated** | Apply the Documentation Standard (§6): frontmatter provenance + version bump + `last_validated` refresh + a Revision History row. Split per the Progressive Disclosure Guide if oversized. |
| **Non‑obvious technical decision** | Write decision log in `plans/archive/<slug>/execution_log.md`. |
| **Mistake that could be repeated** | Add warning to best practices or retro note. |
| **Any intentional change** that modifies repository content (design, doc, code, config) and is **not** a trivial typo fix in a comment or a whitespace‑only change | **Append an entry to the current weekly ledger** `history/YYYY-Www.md`. Substantial changes get `What/Why/Refs`; minor changes get a one‑line note. |
| **External document introduced or found without provenance** | Ask user: *“Is this from an official website? If yes, provide URL and I’ll mark it verified with today’s date.”* After confirmation, add the frontmatter block (or sidecar `.prov.md`) per §6. |
| **Completed task affects future roadmap items** | Update the roadmap. |
| **Epic finished** | Move it to `## Completed Epics`. |

**Logging threshold – important:** The ledger is **not** a verbatim duplicate of `git log`. Do **not** log:
- Single‑character typo fixes in comments.
- Whitespace‑only changes.
- Trivial `.gitignore` adjustments.
Log everything else that a reviewer would care about.

#### Weekly Change‑History Ledger (mandatory)
- [ ] **Log every qualifying change** in `history/YYYY-Www.md` (create file if first change of the week).
  - **Substantial:** full `What / Why / Refs` format.
  - **Trivial / routine:** single one‑line note under the day’s heading.
  - Use tag vocabulary: `[design] [doc] [code] [workflow] [config] [decision] [data]`.
  - Reference commit SHA or archive plan slug if available.
- [ ] At task closure, append a **summary entry** for the completed task.

#### Documentation Standard (mandatory for every doc)
- [ ] When a document is created or updated, apply the frontmatter block (§6): provenance (`official`, `source`), versioning (`version`, `last_validated`), and a Revision History row. Agent‑generated docs default to `official: false`.
- [ ] When an **external** document is first introduced, ask the user: *“Is this documentation from an official website or authoritative source? If yes, please provide the URL.”* Set `official`/`source` from the answer (`unknown` if unconfirmed).
- [ ] For non‑commentable formats (JSON, code), create a sidecar `.prov.md` instead.
- [ ] For existing docs lacking frontmatter, **flag during Phase 0** and plan a future verification task; do not block the current task.

### Phase 3 – Closure

- [ ] **Archive the plan**  
  - Move `UNFINISHED.md` to `plans/archive/YYYY-MM-DD_<slug>/plan.md`.  
  - Create `execution_log.md` / `retro.md` only if the meta‑plan flagged them as needed.  
  - Delete `UNFINISHED.md` (it must not exist at rest).

- [ ] **Final ledger entry**  
  - Ensure all qualifying changes from this session are logged in `history/YYYY-Www.md`.  
  - Append a closure entry summarizing the task.

- [ ] **Update roadmap** if triggered (check completed item, adjust future epics, move finished epics to `## Completed Epics`).

- [ ] **Retrospective** — if the task produced a mistake worth remembering, add an
  entry to `docs/RETROSPECTIVE.md`. If the same mistake is already there, append
  `(recurring)` to its heading; it now owes a rule file under `.ai/01-phases/` and
  a checklist item in `SKILL.md`. `--self-test` reports recurring entries that are
  still uncodified. Two occurrences is the threshold: one is noise, two is a pattern.

- [ ] **Commit & push**  
  `git add -A`  
  `git commit -m "Plan: <slug> – <summary>"`  
  `git push`  
  For a multi‑paragraph message use repeated `-m` flags or `git commit -F <file>`.
  **Avoid heredocs / `-F -` from stdin** (Claude Code's Bash safety layer can
  reject stdin‑fed commands) **and a bare `git commit`** with no `-m` (it can open
  an editor and hang in a non‑interactive shell).

- [ ] **Self‑check:** The agent is **not done** until `UNFINISHED.md` is cleared, the ledger entry is written, and the commit is pushed.

---

## 5. Change‑History Ledger Specification

### 5.1 Directory & Rotation
One file per ISO week: `history/YYYY-Www.md`. Example: `history/2026-W28.md`. The format specification lives in `history/FORMAT.md`.

### 5.2 Entry Format

```markdown
# 2026-W28  (2026-07-06 – 2026-07-12)

## 2026-07-08
### [design] docs/artifact/Scale Indicator.dc.html
- **What:** Reworked ODB reference into full weighing-terminal …
- **Why:** Round-2 UI/UX pass …
- **Refs:** plan `plans/archive/2026-07-08_scale-indicator/plan.md` · commit b30333d

### [code] src/auth.py – minor: fixed login error message
```

**Tag vocabulary:** `[design]` `[doc]` `[code]` `[workflow]` `[config]` `[decision]` `[data]`

**Reference field:** Always include the commit hash (abbreviated). For substantial changes, link to the corresponding plan file using its relative path.

### 5.3 Logging Threshold
- **Log** every intentional change that has a purpose: feature work, bug fixes, refactoring, documentation updates, configuration changes, important decisions.
- **Do not log** trivial typo fixes in comments, formatting-only changes (unless part of a larger intentional formatting PR), or updates to `.gitignore` that don’t affect the project’s logic. Use judgement: if a reviewer would care, log it.

### 5.4 Hook Detection (Stop Hook)
The `Stop` hook uses a per‑session state file to track whether source files were modified and whether the ledger was touched. If the session changed tracked files under `source_directories` but the ledger file wasn’t modified, it emits a reminder. The closure phase (Phase 3) **mandates** the ledger entry for all intentional changes, regardless of directory; the Stop hook’s reminder is a safety net primarily for source‑code modifications. Additionally, whenever the working tree is dirty at Stop the hook records a Phase‑3 breadcrumb in `plans/UNFINISHED.md` (§7.3) so an interrupted closure is never lost. The reminder may block a bounded number of times (`stop_hook.max_blocks`), but always yields afterward so a session can end.

---

## 6. Documentation Standard

Every document created or updated under the configured `documentation_directories`
carries a single **YAML frontmatter block** (provenance + versioning + retrieval
metadata) and a visible **Revision History** table. This unifies what were once two
mechanisms (an HTML `SOURCE-PROVENANCE` comment for provenance and an ad‑hoc version
header) into one machine‑readable block that the Progressive Disclosure retrieval
script already parses. A reusable skeleton lives at `templates/docs/DOC_TEMPLATE.md`.

### 6.1 Frontmatter block (for Markdown / HTML docs)
Place at the very top of the file:

```markdown
---
title: <Title>
version: 1.0                     # bump MINOR for content, MAJOR for restructure
last_validated: YYYY-MM-DD       # date you last re-confirmed the CONTENT is correct
official: false                  # true | false | unknown
source: agent-generated          # URL | agent-generated | user-provided, origin unknown
tags: [<retrieval tags>]
applies_when: "<when this doc is relevant>"
estimated_tokens: <int>          # keep honest; feeds retrieval + the token-budget lint
---
```

**The `official` field:** set `official: true` only for documents reviewed and
approved via the project's governance process (e.g. `GUIDE.md`, ADRs). Use
`official: false` for drafts, agent‑generated docs, personal notes, or exploratory
checkpoints. Use `official: unknown` when the origin cannot be confirmed yet.

### 6.2 Sidecar frontmatter (for JSON, code, and other non‑commentable formats)
Frontmatter is impossible in these formats → create a companion `.prov.md` in the
same directory carrying the same fields. Example `config.json` → `config.json.prov.md`:

```markdown
# Provenance for config.json
- version: 1.0
- last_validated: 2026-07-10
- official: false
- source: agent-generated
- notes: Production database credentials – should be reviewed
```

### 6.3 Versioning & Revision History
Directly under the title, restate the version and keep a visible changelog table:

```markdown
# <Title>
**Version 1.0** — *<one-line scope>*

## Revision History
| Version | Date       | Change   |
|---------|------------|----------|
| 1.0     | 2026-07-10 | Initial. |
```

On any non‑trivial edit: bump `version` (MINOR for content, MAJOR for restructure),
add a Revision History row, and log the change to the weekly ledger. Refresh
`last_validated` **only when you re-confirm the content itself is correct** — it
records the last content review, not the last keystroke. A mechanical or
frontmatter-only edit (e.g. backfilling provenance fields, fixing a typo, retagging)
still bumps `version` and adds a history row, but leaves `last_validated` unchanged so
the field never overstates how recently the content was validated. Version namespaces
are **per‑document and independent** — two docs sharing a number (e.g. `v4.x`) are
unrelated lineages, not a shared series.

**Bounding the Revision History (so it never becomes the growth vector).** The
in‑file table is a convenience, not the system of record — `git log` and the weekly
ledger are. Keep it small. When the table exceeds **~8 rows**, or when the doc folds
into a folder for any reason (§6.4), relocate the full history to a sibling
`CHANGELOG.md` and leave only the latest **≤3 rows plus a link** in the live doc.

### 6.4 Folding a document into a folder
Do not restate a line threshold here — defer to the **Progressive Disclosure
Documentation Guide** (`docs/Progressive Disclosure Documentation Guide.md`). A doc
**folds** from a flat `docs/<name>.md` into a `docs/<name>/` folder when either
trigger fires:
1. it **splits** — it violates that guide's **"Rule of One Question"** (§5) or
   exceeds its layer's **token budget** (§2, e.g. Procedural ≤ 2,000, Semantic
   knowledge file ≤ 5,000); or
2. its in‑file **Revision History** grows past **~8 rows** (history now rivals the
   content it documents).

On folding: `index.md` holds the canonical frontmatter and current truth; each split
child carries its own lightweight frontmatter plus a link back. The doc's full
history moves to a sibling **`CHANGELOG.md`** (copy `templates/docs/CHANGELOG_TEMPLATE.md`),
and `index.md` keeps only the latest **≤3 Revision History rows plus a link** to it.

The `CHANGELOG.md` is a **sibling peer** of `index.md`, *not* a split‑child: it is
not listed in `index.md`'s child index and carries no `parent:` link — it only
relocates history. It is Episodic (never loaded): it carries `applies_when: "Never
load…"` **and** the machine‑readable `exclude_from_ai: true` flag, which the
Progressive Disclosure retrieval script honours by skipping the file before scoring.
Its `estimated_tokens` therefore stay **outside** the active token budget; only
`index.md` counts. Recalculate `index.md`'s `estimated_tokens` downward after folding.

> **See also (Progressive Disclosure Guide):** for large/monorepo projects, that
> guide's **§3.1** documents an optional distributed **`SCOPE.md`** scaling tier
> (per‑directory *static* scope — distinct from the single root dynamic
> `CONTEXT.md`), and **§5.1** adds content‑quality rules (Show‑Don't‑Tell code
> pairs, textual‑twin diagrams). Both sit under this same §6 Documentation Standard.

### 6.5 When to add / update
- Document created or updated → apply §6.1–6.3 (and fold into a folder per §6.4 if it
  outgrows one question / its token budget, or its Revision History passes ~8 rows).
- External document introduced → ask for confirmation, then set `official`/`source`.
- Agent‑generated documentation → `official: false`; set `last_validated` to today
  only when the content is genuinely authored/reviewed now (not for a mechanical
  frontmatter backfill on pre‑existing content — see §6.3).
- Existing files without frontmatter → flagged during Phase 0, filled later (non‑blocking).
- **Defer option:** if the user cannot confirm origin immediately, mark `official: unknown`.

---

## 7. Hook System Architecture

### 7.1 Dispatcher
A single Python script (`hooks/workflow_hook.py`) is invoked for `SessionStart`, `PreToolUse`, `PostToolUse`, and `Stop`. It reads the event from stdin JSON, loads the project’s `workflow_config.json`, and branches to the appropriate handler. Every handler is wrapped in a try‑except that ensures the process exits with code 0 (fail‑soft).

Fail‑soft cuts both ways once one of those handlers is a guard: a crash in `PreToolUse` means the tool call proceeds. The dispatcher **fails open** and is not a security boundary. §7.5 states the limits; the `enforcement_note` on every artifact that depends on it repeats them, so `live` is never read as “unbypassable”.

### 7.2 Per‑Session State
State is persisted across invocations using a temporary JSON file: `Path(tempfile.gettempdir()) / "workflow_hook_state_{session_id}.json"` (`session_id` sanitized). This file contains:
- `source_changed` (bool) – any edit to a configured source directory this session.
- `ledger_touched` (bool) – the current week’s ledger file was created or modified during the session.
- `stop_block_count` (int) – how many times the Stop hook has blocked.
- `main_branch_detected` (str | null) – the auto-detected default branch, memoised on the first `Stop` so one session probes git at most once (see §7.4).
- Timestamp of session start (for stale cleanup).

`SessionStart` clears stale state files older than 24 hours and resets flags.

### 7.3 Hook Events

#### SessionStart
- Reads git branch, dirty status, ahead/behind info.
- Runs environment checks using paths and version flags from config (respecting `null` version_flag to only verify existence).
- Parses the `**Next action:**` line from the configured roadmap file.
- **F5 update check (opt-in):** when `workflow_update_check.enabled` is true and the configured `submodule_path` is a linked git repo, fetches it at most once per day (gated by `.ai/.workflow_check_date`) and, if it is behind `{remote}/{branch}`, appends a `🔄 Workflow updates available` notice. Detection only — never auto-applies. Off by default; see §9.
- Outputs: `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "..."}}` and optionally a `sessionTitle`.

#### PreToolUse
- Matcher: `Bash|PowerShell` — both, because `Bash(...)` and `PowerShell(...)` are separate permission namespaces and a Bash‑only guard is bypassed by the other tool.
- Splits the command on the separators the permission matcher recognises (`&&`, `||`, `|&`, `;`, `|`, `&`, newline) and evaluates every subcommand, so a prohibited call cannot hide behind a benign one.
- Emits `permissionDecision: "deny"` for a force‑push whose destination resolves to a protected branch, and for a deletion aimed at `tier0_guard.protected_paths`.
- Emits `permissionDecision: "ask"` for a history rewrite (`--amend`, `rebase`, `reset --hard`, `filter-branch`) and for heredoc stdin (`<<`, `-F -`, `--file=-`, bare `git commit`) — cases where the command alone cannot settle the question. A `deny` anywhere outranks an `ask` anywhere.
- Emits **nothing** otherwise. Silence defers to the normal permission flow; returning `"allow"` would *approve* the call and auto‑approve every shell command in the session.
- Holds no session state and consults git only after a force flag has already been parsed — it runs before every shell call, so it must cost nothing on the ones that are not pushes.
- Full contract, including the guard table and the known limits, in `schemas/hook_contract.md`. Design rationale in §7.5.

#### PostToolUse
- Matcher: `Edit|Write|MultiEdit`.
- Extracts all touched file paths (handles `MultiEdit`’s `edits` array).
- If any path falls under a source directory, sets `source_changed` flag in state.
- If any path falls under the ledger directory, sets `ledger_touched` flag.
- Once per session, if source changed but no documentation file from the configured doc directories has been touched, emits an advisory nudge: *“Consider updating docs and the weekly ledger if this change is worth tracing.”*
- Outputs: same `hookSpecificOutput` structure; advisory only.

#### Stop
- Reads current state file.
- If `stop_block_count >= max_blocks` (from config, default 2) or if `stop_hook_active` is true in the event payload, exits without blocking.
- Otherwise, checks conditions:
  - If working tree is dirty on a branch other than the resolved main branch (§7.4), prepare a commit reminder.
  - If `source_changed` is true but `ledger_touched` is false, prepare a ledger reminder (for source‑code changes only; closure still mandates logging everything).
  - If the working tree is dirty on **any** branch, write a Phase‑3 breadcrumb to `plans/UNFINISHED.md` (see below) — this happens whether or not the hook blocks.
- If any reminder is needed, increments `stop_block_count` in state, outputs `{"decision": "block", "reason": "..."}`, and exits 0. If no reminders, exits 0 with no output (allowing the session to end).

**Phase‑3 breadcrumb:** on a dirty tree the hook writes/refreshes `plans/UNFINISHED.md` (timestamp, branch, `git status --porcelain` file list, pending closure steps) so the next `SessionStart` (F4) surfaces the unfinished work — durable even if the reminder is ignored or the session is force‑closed. The file starts with the marker `<!-- workflow-hook: auto-breadcrumb -->`; the hook overwrites only its own marked breadcrumb and **never** clobbers a human‑authored `UNFINISHED.md`. This directly closes the failure mode where a session ends mid‑closure leaving a dirty tree and no trace.

**Important:** The Stop hook’s *ledger* detection is session‑scoped, not `git diff` against HEAD (which would include pre‑session changes). This ensures we only nag for things done *this session*. The dirty‑tree commit reminder and breadcrumb use live `git status`.

**Why the flags alone were not enough.** `source_changed` and `ledger_touched` are set by `PostToolUse`, which fires only for `Edit|Write|MultiEdit`. Anything written another way is invisible to it — and both failure directions showed up in practice within a day of the guard shipping. A ledger appended by a shell redirect reads as untouched, so the reminder fires on a session where the entry was already written, committed and pushed; a reminder that fires when the work *was* done trains you to dismiss it. Worse, a source file rewritten by `sed -i` reads as unchanged, so the reminder never fires at all.

So the flags are now a fast path, backed by a modification‑time check against `session_start_ts` (`stop_hook.mtime_fallback`, default on). That stays session‑scoped as this section requires, while being blind to *how* a file was written. Claude Code’s `FileChanged` event would be the better mechanism — it watches the disk and so sees writes from any process — but its matcher is a list of **literal filenames**, and our ledger filename rolls over every Monday; a static watch list would go stale in a week, which is the mistake already recorded in `docs/RETROSPECTIVE.md`. If that matcher ever accepts globs, revisit it (see `ROADMAP.md`).

The source walk returns on the first file newer than the threshold and gives up after `mtime_scan_limit`, so it is bounded in both directions; it runs at every `Stop`. Two honest limits: `git checkout`/`pull` bump mtimes, so a pull touching the ledger can suppress a real reminder and one touching source can raise a spurious one; and if the state file is lost, `session_start_ts` becomes *now*, every mtime reads as older, and the reminder fires — the conservative direction.

### 7.4 Resolving the main branch

The dirty‑tree commit reminder needs to know which branch is “home”, because a dirty tree there is expected rather than a missed Phase‑3 closure. Assuming `main` mis‑fires on the many repositories whose default branch is `master`, `trunk`, or `develop`, so the hook resolves it in this order:

1. **Explicit pin** — a non‑empty `stop_hook.main_branch` always wins. Detection never overrides a deliberate config value.
2. **Auto‑detection** (`stop_hook.main_branch_autodetect`, default **true**) — reads the local ref `refs/remotes/<main_branch_remote>/HEAD` via `git symbolic-ref`. This is a local ref read with **no network access**, written by `git clone` and refreshable with `git remote set-head origin --auto`.
3. **Optional remote probe** — only when `stop_hook.main_branch_probe_remote` is true, falls back to `git remote show <remote>` and parses its `HEAD branch:` line. This **contacts the remote**, so it is off by default: the Stop hook must never stall session close on a network round‑trip.
4. **Default** — `main`.

The resolved value is memoised in the session state (`main_branch_detected`), so a session probes at most once even across repeated `Stop` events, and the probe is skipped entirely when `Stop` short‑circuits on `stop_hook_active` / the block cap. Fail‑soft throughout: a git error at any step falls through to the next candidate.

> **Edge case:** a repo with no remote (or a stale `origin/HEAD`) yields no detection and lands on `main`. If such a project's default branch is `master`, pin `stop_hook.main_branch` explicitly — or run `git remote set-head origin --auto` once to populate the ref.

### 7.5 Why the Tier‑0 guard is a hook and not a deny rule

Claude Code's `permissions.deny` is the stronger mechanism for anything a pattern can express: deny is evaluated before ask and allow, it applies in every permission mode including `bypassPermissions`, and a `PreToolUse` hook returning `"allow"` cannot loosen it. Where a pattern suffices, use a deny rule.

It does not suffice here, for three reasons that are properties of the prohibitions rather than of the syntax:

1. **Arguments reorder.** `Bash(git push --force*)` matches a literal prefix, so it misses `git push origin main --force` and `git push -f`. The docs warn directly that patterns constraining command *arguments* are fragile.
2. **A deny rule carries no exceptions.** One broad enough to stop a force‑push to `main` also stops the same push to a topic branch you own. But the prohibition is *never force‑push a **shared** branch* — and whether a branch is shared is a fact about the repository, not about the command string.
3. **Two shells.** `Bash(...)` and `PowerShell(...)` are separate namespaces. A rule list written for one is bypassed by the other.

So the guard parses. Two decisions come out of it, and the split is the design:

- **`deny`** where the prohibition is unambiguous from the command plus the repository — the destination branch is protected, the deletion target is inside the audit trail.
- **`ask`** where it is not. Whether a commit is already published, or whether a particular heredoc is the dangerous kind, cannot be read off the command. Denying every candidate would block legitimate work; guessing would be worse. An `ask` still enforces — the call cannot proceed without a human — while a false positive costs one keystroke instead of a wall.

That second decision is what made the guard worth building. `rule-no-heredoc-stdin` v1.0 declined a hook on the grounds that *“the false‑positive cost on legitimate heredocs was judged higher than the failure it prevents.”* That weighed a hard block. `ask` inverts the trade.

**Limits, stated because a tier that overstates itself is the failure this library exists to prevent.** The dispatcher is fail‑soft, so an exception in the guard allows the call. Subcommand splitting does not honour quotes, so a separator inside a quoted string yields an extra fragment — over‑reporting, the safe direction. In `dontAsk` mode an `ask` becomes a silent block rather than a prompt. And the guard sees tool calls only, never a terminal opened outside Claude Code: OS‑level enforcement is the sandbox's job.

One prohibition deliberately did **not** move. `prohibition-commit-secrets` stays `convention` because the guard sees the command, not the file contents being committed — it could only ever catch a secret typed inline, which would be enforcement theatre. Real coverage means scanning `git diff --cached`; that is on the roadmap, not claimed in the library.

---

## 8. Configuration & Project Integration

### 8.1 Adopting the Workflow in a New Project
1. Add the workflow repository as a Git submodule:  
   `git submodule add <workflow-repo-url> .claude/workflow-core`
2. Copy `templates/workflow_config.json` to `.claude/workflow_config.json` and adjust paths/feature flags.
3. Merge `templates/settings.json.hooks` into `.claude/settings.json` — the `hooks` block
   **and** `permissions.defaultMode`. Merge, don't copy: the file is a fragment, and
   overwriting discards your own permissions and env.
   **Then verify the guard is live**: attempt `git push --force` to your main branch and
   confirm it is *denied*. If it is allowed, the `PreToolUse` entry did not take, and all four
   Tier-0 prohibitions are documentation only.
4. Copy the skills: `cp -r .claude/workflow-core/templates/skills/* .claude/skills/`. Claude
   Code discovers skills only under `.claude/skills/`, so the submodule's own copy is not
   loaded. Re-copy after each update.
5. Add `.claude/settings.local.json` to your `.gitignore` — it holds personal permission
   grants and must not be committed.
6. Include the fragment `templates/CLAUDE.md.fragment` in the project’s `CLAUDE.md`.
7. Initialize the ledger directory: `mkdir history && cp .claude/workflow-core/templates/history/FORMAT.md history/FORMAT.md`

### 8.2 Updating the Workflow
From the project root:
```bash
cd .claude/workflow-core
git pull origin main
cd ../..
git add .claude/workflow-core
git commit -m "chore: update workflow-core to v4.1"
```
Any breaking changes will be documented in the workflow’s `CHANGELOG.md`. Projects may need to adjust their `workflow_config.json`.

### 8.3 Overriding Hook Behaviour
Projects can override hook functionality without forking the workflow:
- Custom hooks can be placed in `.claude/hooks_local/` and referenced in `settings.json`.
- Feature flags (e.g., `ledger.enabled: false`) disable whole features.
- The hook script accepts `--dry-run` for testing.

---

## 9. Daily Workflow Update Check

Embedded in Phase 0 (F5), but detailed here for reference.

**Automation (opt-in):** setting `workflow_update_check.enabled: true` in `workflow_config.json` makes the `SessionStart` hook perform steps 1–3 and 6 below automatically (fetching at most once per day and injecting the notice). It is **off by default** and **detection-only** — the hook never runs `git submodule update`. When disabled (the default), the agent performs the check manually as described. Config keys: `enabled`, `submodule_path` (default `.claude/workflow-core`), `remote` (default `origin`), `branch` (default `main`).

- **State file:** `.ai/.workflow_check_date` contains the date of the last check (format `YYYY-MM-DD`). Create it only after the submodule is present.
- **Procedure:**
  1. If `.claude/workflow-core` directory is missing, skip check (note the workflow is not yet linked).
  2. If today’s date differs from the file, `cd .claude/workflow-core && git fetch origin`.
  3. Compute commits behind: `git rev-list --count HEAD..origin/main`.
  4. If > 0, inform user: *“Workflow updates available (X new commits). Review and update?”*
  5. If user approves, `git submodule update --remote --merge` and validate hooks.
  6. Update the date file.
- This check runs at most once per day per project, preventing version drift.

---

## 10. Workflow Improvement & Contribution Process

The workflow is a living document. Any project using it is encouraged to propose improvements.

### 10.1 Detection & Classification
When the agent (or user) discovers a flaw, missing trigger, or potential improvement:

- [ ] **Identify the issue** (e.g., hook bug, missing conditional trigger, unclear documentation).
- [ ] **Classify its criticality:**

| Criticality | Definition | Immediate action required? |
|-------------|------------|-----------------------------|
| **High** (a.k.a. **Critical**) | Workflow fails to enforce invariants, may cause data loss, session‑breaking bug, security hole. | Yes – fix locally now, submit PR. |
| **Medium** | Missing trigger, inefficient process, documentation ambiguity, non‑critical logic error. | No – propose a plan, do not apply until approved. |
| **Low** | Cosmetic, wording, minor edge‑case improvement. | No – create issue or low‑priority branch. |
| **Non‑critical** | Observation, suggestion, future enhancement. | No – create issue only. |

> **On the word “critical”:** the top tier is named **High**. Some teams call it
> **Critical** — they mean the same level (data loss / security / session‑breaking).
> There is no separate tier above High.

- [ ] **Log the discovery** in the project’s own `history/YYYY-Www.md` (tag `[workflow]`).

### 10.2 High‑Criticality (a.k.a. Critical) – Immediate Fix
- **Local fix:**  
  `cd .claude/workflow-core && git checkout -b fix/<short-description> && git commit -m "fix(high): <description>" && git push origin fix/<short-description>`
- **Open a Pull Request** in the central workflow repo. PR must explain the flaw, why it’s high, and the fix.
- **Apply locally now:** The project may immediately use the fix by staying on that branch. The submodule will be officially updated after merge.
- Notify user.

### 10.3 Medium‑Criticality – Proposal & Plan
- **Create proposal branch:** `proposal/<description>`. Include a detailed plan (markdown file or commits).
- **Push and open a PR** with clear title and explanation.
- **Do not apply locally** until the PR is merged (unless user explicitly requests).
- If the proposal involves documentation, update skill references or spec addendum in the same branch.

### 10.4 Low / Non‑critical – Report Only
- Open an issue: `gh issue create --title "..." --body "..." --label low` (or `non-critical`).
- Optionally push a branch with a draft fix but do **not** create a PR (leave for maintainer).

### 10.5 Proposing a New Checklist Item (New Trigger / Step)
- Treat as Medium‑Criticality. In the proposal branch, **add the new item** to the relevant section of this guide (or `SKILL.md`) with rationale and examples.
- Describe expected behaviour and interaction with existing steps.
- Submit PR and wait for approval; do **not** enforce locally until merged.

### 10.6 After Contribution – Sync & Cleanup
- Track the PR/issue in the project’s roadmap if significant.
- After the PR is merged, the daily update check will detect new commits. Update submodule, verify fix, and log the update in the ledger.
- If a high‑criticality fix was applied locally before merge, ensure the submodule fast‑forwards cleanly.

---

## 11. Agent Quick‑Reference Checklist

The following is a condensed, one‑page checklist for the AI agent. It mirrors the full phases above.

**Phase 0**
- [ ] Git fetch & rebase, note dirty tree.
- [ ] Check configured tools (respect `version_flag` null = existence check only).
- [ ] Load living docs, check for missing provenance blocks.
- [ ] Surface unfinished plan & next roadmap item.
- [ ] Daily workflow update check (skip if submodule absent; create date file only once submodule exists).

**Phase 1**
- [ ] Assess task scope, documentation impact, provenance, ledger needs.
- [ ] Chunk large tasks using roadmap.
- [ ] Produce bullet task‑specific checklist; optionally confirm with user.

**Phase 2 – For each task item**
- [ ] Implement, then run linter & tests.
- [ ] Apply triggers:
  - Ledger entry for every intentional change that is **not** a trivial typo fix in a comment or a whitespace‑only change.
  - Doc updates per trigger table.
  - Provenance for new external docs.
  - Roadmap updates if needed.
- [ ] Log obstacles and update plan if necessary.

**Phase 3**
- [ ] Archive plan (move `UNFINISHED.md` → archive, delete original).
- [ ] Final ledger summary entry.
- [ ] Roadmap update.
- [ ] Commit & push.
- [ ] Confirm all three conditions met: no `UNFINISHED.md`, ledger written, pushed.

**Hooks will remind you – treat them as helpful nudges.**

---

## 12. The Imported 21-Step SOP → Phase 0–3 Mapping

The [Self-Growing Checklist Ecosystem v14](docs/self-growing-checklist-ecosystem/index.md)
specifies a 21-step Master Execution Checklist. **It is not adopted as a replacement
numbering** — Phase 0–3 stays canonical, and renumbering would break every archived
plan, ledger entry and hook reference for no behavioural gain. Instead each step maps
to the phase that already owns it, with its enforcement tier attached.

Tiers: **live** = a hook or test enforces it · **convention** = the agent follows it,
nothing blocks · **declarative** = recorded only, not enforceable in this runtime.
The reasoning behind each assignment is in
[`docs/governance-integration-decision.md`](docs/governance-integration-decision.md).

| v14 step | What it asks for | Lands in | Tier |
|---|---|---|---|
| 1 | Synchronize source control | Phase 0 · F1 | convention |
| 2 | Check for pending work | Phase 0 · F1/F4 | live |
| 3 | Check pending ratifications | Phase 0 · F4 (`UNFINISHED.md`) | live |
| 4 | Validate the build environment | Phase 0 · F2 | live |
| 5 | Check security vulnerabilities | Phase 2 (conditional on a lockfile) | convention |
| 6 | Draft high-level plan | Phase 1 | convention |
| 7 | Retrieve similar past context | Phase 0 · F3 + the weekly ledger | convention |
| 8 | Load domain checklists | Phase 0 · F3 + `.ai/` manifests | convention |
| 9 | Identify knowledge gaps / research | Phase 1 | convention |
| 10 | Validate new knowledge | Phase 2 · Documentation Standard | live |
| 11 | Split plan into stages | Phase 1 | convention |
| 12 | Iterative technical audit | Phase 2 · lint + tests | live |
| 13 | Performance scrutiny | Phase 2 (optional) | convention |
| 14 | Verify reversibility | Phase 2 · reversibility item | live |
| 15 | Check for agent loops | Phase 2 · `PostToolUse` loop detection (§7.3) | live |
| 16 | Verify test coverage | Phase 2 · test suite | live |
| 17 | Stage and commit | Phase 3 | live |
| 18 | Push & open PR | Phase 3 | convention |
| 19 | Generate validation checklist | Phase 3 · the user reviews | convention |
| 20 | Wait for human sign-off | Phase 3 · the user approves | convention |
| 21 | Retrospective & grow the library | Phase 3 · retrospective item | live |

Steps with no row here — cryptographic identity, delegation, shadow-AI detection,
sandboxed execution, RAG quality metrics — are **declarative or dropped**. They
presuppose an agent fleet, key infrastructure, or API access that this runtime does
not have (§14). They are recorded in `.ai/` with the reason attached rather than
faked.

---

## 13. The Governance Library (`.ai/`)

A chunked rule library instantiated from v14 §5. Small files, one manifest per
folder, loaded on demand — the same progressive-disclosure idea as §6, applied to
rules instead of prose.

```
.ai/
├── 00-system/              config, agent registry, autonomy boundaries, maturity
│                           tracker, checklist-selection.json (the one loading table)
├── 01-phases/              one rule file per workflow step (Phase 0-3 + v14 step mapping)
├── 02-market-rules/        immutable golden rules; prohibitions/ is Tier 0
├── 03-planning/            plan review, Phase 1  — 5 rules, 31 sourced items
├── 05-domains/             code review, Phase 2  — 10 rules, 80 sourced items
├── 06-components/          blueprints            — empty, grows per retrospective
├── 08-behavioral-metrics/  hook-written JSONL, and what is deliberately absent
├── 09-variants/            forks awaiting ratification
├── 10-ratification-archive/ decision history
└── GROWTH.md               the three growth protocols + the self-hardening rule
```

**Every artifact declares an `enforcement_status`.** The rule is that no artifact
may imply enforcement it doesn't have: a declarative field is written as `null` with
its reason attached, never as a plausible-looking fake value. If you cannot name the
hook or test that makes a rule *live*, it is `convention` — say so and mean it.

**`live` covers two strengths, and the artifact must say which.** A guard that returns
`deny` blocks outright. One that returns `ask` blocks until a human answers — and the
human may wave it through, which happened within an hour of the guard shipping: the
heredoc guard fired correctly, the prompt was approved, and the rule was broken anyway.
Both are `live` by the definition above, because both produce a visible signal. They are
not the same promise. So any artifact enforced by a `guard_*` symbol carries an
`enforcement_mode`:

| Strength | Meaning | Held to the code by |
|----------|---------|---------------------|
| `deny` | The call is blocked. No approval path. | `TestEnforcementModeMatchesGuard` — feeds the guard a command that must trip it and asserts the returned decision equals the declared mode |
| `ask` | The call is blocked *until a human answers*; the answer may be yes. In `dontAsk` mode it becomes a silent block. | the same test |

Flip an artifact to `ask` while its guard still denies and the suite goes red. The tier
says a control exists; the mode says how much it promises.

**And the declaration is tested.** `tests/test_governance_library.py` turns each of
those sentences into an assertion: a `live` artifact must carry `enforced_by`, a list
of `path::symbol` references resolved against the actual source; a `convention` must
carry an `enforcement_note` saying what the real mechanism is; a `declarative` block
must carry a `reason` and keep its values null. It also holds the manifests to the
files on disk, `risk_source`/`risk_weight` to the CISA taxonomy in §11.3 of the
imported spec, this section's step-mapping table to `01-phases/manifest.json`, and
`.ai/` to its `templates/ai-library/` mirror. Written after an audit found seven
taxonomy violations, a false step mapping and eight untraceable `live` claims in a
library that had been correct-looking prose for exactly one commit.

**Three prohibitions are now `live`, and one deliberately is not.** The Tier-0 set
shipped as `convention` — prose the agent honours and the user reviews. The
`PreToolUse` guard (§7.5) moved force-push-to-a-shared-branch and deleting the audit
trail to a `deny`, and rewriting published history to an `ask`; `rule-no-heredoc-stdin`
moved with them. `prohibition-commit-secrets` stayed `convention` because the guard
sees the command, not the file contents being committed — the honest tier for a
control that would only ever catch a secret typed inline. Every one of those artifacts
states in its `enforcement_note` which decision it emits and that the dispatcher fails
open, so `live` is never read as *unbypassable*.

**`05-domains/` holds review checklists, written as questions.** *"Does this class have
one reason to change?"* — not *"use an interface for every service"*. The distinction is
the point: a question makes the agent look at the code and keeps its judgement intact,
while a prescription tells it what to type and stops being right the moment the codebase
differs from the one the rule was written for. All `convention` — nothing mechanically
decides whether a class has one responsibility, and the checklists say so. Harvested by
research rather than from a mistake, which `GROWTH.md` documents as a fourth growth
protocol; a researched rule is *proposed* until a human ratifies it. Each is trialled
against real code before being kept, because a checklist that finds nothing is too vague to
be worth loading.

**`03-planning/` reviews the plan, before any of that.** Ten categories of code review
still cannot see a defect one level up: `05-domains/` reviews code *against* the plan, so
it will confirm that a well-built thing was built well when the thing should not have been
built at all. Until this folder existed, `rule-task-checklist` told the agent to produce a
plan checklist and supplied nothing to interrogate it with — **a plan was reviewed by
nothing.** Five rules, 31 items, answered at Phase 1: is the problem stated separately from
the solution, is each acceptance criterion verifiable and singular, what is the rollback,
which alternative was rejected, and can the proposed check actually fail. Never gated on
tech stack — a plan's problem statement is no better for being written in Go.

**Sixteen categories, 119 items, every one sourced.** Each item cites a document with an
authority tier, and its `confidence_level` is *derived* by
`hooks/workflow_hook.py::derive_confidence` and recomputed by test — never typed by hand.
An item that cannot be sourced does not ship. `--self-test` warns when an item's
`last_validated` passes `revalidation_interval_days`. The full framework, both folders, and
the citation defects found along the way — including **IEEE 1012-2016, superseded by
1012-2024** — are in [`docs/checklist-system.md`](docs/checklist-system.md).

**Conditional loading keeps this affordable.** The selection rules live once, as data, in
`.ai/00-system/checklist-selection.json`; both skills read them rather than restating them,
and both folders are selected from the one table. A rule loads when its `workflow_phase`
matches the phase in progress, its `task_size_required` includes the size declared at Phase
1, *and* its `tech_stack_required` is empty or intersects the project's stack. Measured: a
typo fix loads 9 items, a new REST API 34, and a project with no database in its stack
loads no database rule at all — which is what makes the §6.4 token budget hold.

**`06-components/` is still empty, and stays that way until a pattern earns a blueprint.**
`BLUEPRINT_SCHEMA.md` defines the shape; the bar is that the pattern has already shipped
and survived review. A blueprint written in advance is a guess with a filename — the same
error as a rule harvested from imagination. See `.ai/GROWTH.md` for all four protocols and
the self-hardening rule (a mistake recorded twice becomes structure).

**Provenance.** `00-system/` config files carry `.prov.md` sidecars per §6.2. Rule
files don't — they embed a `provenance` block in the JSON, which is what the sidecar
convention exists to substitute for. One provenance record per artifact, in the
artifact wherever the format allows it.

**Health.** `python hooks/workflow_hook.py --self-test` validates the config and
reports a governance maturity level (1–5) derived from real checks, writing
`00-system/maturity-tracker.json`. The level is reported, never enforced — a young
repository is not a broken one.

---

## 14. Runtime Assumptions

The workflow is shaped by what its runtime can actually do. Verified against
official sources on 2026-08-04; **re-check these before trusting §12's tiering**,
because two of them have already moved once.

| Fact | Source |
|------|--------|
| Claude Pro ($20/mo, $17 annual) **includes Claude Code** | [claude.com/pricing](https://claude.com/pricing) |
| Claude Code authenticates with the subscription login. A set `ANTHROPIC_API_KEY` **overrides it** and bills per token | [support 11145838](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan) |
| Sonnet 5 is the default; Opus 5 is *"the strongest model on Claude Pro"* | [Opus 5 announcement](https://www.anthropic.com/news/claude-opus-5) |
| **On Pro, Fable 5 bills pay-as-you-go usage credits** — it is not covered by plan limits | [support 15424964](https://support.claude.com/en/articles/15424964-claude-fable-5-on-your-plan) |
| `opus` → Opus 5 on the Anthropic API, but **only on Claude Code v2.1.219+** (before that it resolved to Opus 4.8) | [model-config](https://code.claude.com/docs/en/model-config) |
| Rolling 5-hour session window + weekly caps, **separate weekly cap for Opus**, shared with the Claude app | [costs](https://code.claude.com/docs/en/costs) |

**Model policy.** Sonnet 5 for routine work; `/model opus` for hard passes.
**Fable 5 is a paid escalation on Pro and must never be a shipped default** — not in
a skill, not in subagent frontmatter, not in an `ANTHROPIC_DEFAULT_*` variable.

**What the constraints rule out.** No API key means no embeddings, no vector search
and no judge model, so v14's RAG quality metrics are dropped rather than deferred.
One local agent means cryptographic identity, delegation and shadow-AI detection have
no counterparty. Finite, separately-metered quota makes "chunk large tasks" a cost
control, not just hygiene.

**The `ANTHROPIC_API_KEY` trap.** A key left in the environment silently moves
billing off the subscription. `SessionStart` and `--self-test` both warn about it.
Warning only — API-key auth is legitimate, just rarely what you meant here.

---

## Appendix A: Templates

### ISO‑Week Filename
`history/YYYY-Www.md` (e.g., `history/2026-W28.md`)

### Documentation Frontmatter (Markdown) — see §6 and `templates/docs/DOC_TEMPLATE.md`
```markdown
---
title: <Title>
version: 1.0
last_validated: YYYY-MM-DD
official: false            # true | false | unknown
source: agent-generated   # URL | agent-generated | user-provided, origin unknown
tags: [<retrieval tags>]
applies_when: "<when this doc is relevant>"
estimated_tokens: <int>
---

# <Title>
**Version 1.0** — *<one-line scope>*

## Revision History
| Version | Date       | Change   |
|---------|------------|----------|
| 1.0     | YYYY-MM-DD | Initial. |
```

### Ledger Entry (Full)
```markdown
## YYYY-MM-DD
### [tag] path/to/file
- **What:** …
- **Why:** …
- **Refs:** plan <slug> · commit <sha>
```

### Ledger Entry (One‑liner)
```markdown
### [code] src/utils.py – minor: fixed typo in error message
```

### Contribution Branch Naming
- `fix/<description>` for high‑criticality fixes
- `proposal/<description>` for medium changes
- `low/<description>` for low/non‑critical (optional)

---

*End of Version 5.0 – The Adaptive Self‑Correcting Workflow. The single source of truth, powered by its community.*