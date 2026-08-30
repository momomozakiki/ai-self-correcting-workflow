# Git — golden rules (new project)

Status: drafted by orchestrator 2026-08-30, unreviewed
Applies when the repository does not exist yet, or exists with no commits. From the first push
onward, `existing-project.md` is the one that applies — it covers branching, syncing and
everything that has a base to verify against.

## Before `git init`

- [ ] `git rev-parse --show-toplevel` — if it prints a path, you are inside a repository
      already and about to nest one inside it. Nested repos are invisible to the outer `git
      status` and their content silently never ships.
- [ ] Choose the default branch name **before** the first commit: `git init -b main`. Renaming
      it afterwards is cheap locally and a coordination cost for everyone who has cloned.
- [ ] Decide what must never be committed before anything is committed — credentials, build
      output, local tooling state. Git makes adding easy and removing expensive.

Sources: Pro Git, 2nd ed. (Chacon & Straub, 2014) ch.2; `git-init(1)` — `-b` requires git 2.28
(2020) or newer.

## The first commit

- [ ] Write `.gitignore` **before** the first `git add`, not after. A file committed once is in
      the history whether or not it is later ignored, and removing it means rewriting published
      history — which this repository's Tier-0 prohibitions forbid outright.
- [ ] Before `git add -A`, check what it would sweep in: `git status --short`. Machine-generated
      and transient session state is the usual casualty, and a small tree is the cheapest place
      to catch it.
- [ ] Add a README whose **first sentence** says what the project is for. It is the only
      documentation guaranteed to be read.
- [ ] Choose a licence, or state deliberately that there is none. An absent licence is not
      "permissive by default"; it is all rights reserved.

Sources: Pro Git, 2nd ed. (2014) ch.2; `.claude/rules/repo-conventions.md` (commit hygiene,
2026-08-29) — `git add -A` has swept transient session state into this repository twice.

## Writing the commit

- [ ] `git commit -m` (repeatable for multiple paragraphs) or `-F <file>`.
- [ ] **Never** `-F -`, a heredoc, or a bare `git commit`. Escapes mangle silently, and a bare
      invocation opens an editor that an automated session cannot drive.
- [ ] The message says **why**, not what — the diff already says what. On a first commit the
      why is usually "what this repository is for", which is worth one paragraph.

Sources: Incident (recurring, ×2, 2026-08) — heredoc stdin mangled commit content without
error; codified in `.claude/rules/repo-conventions.md`.

## Before the first push

- [ ] Create the remote **empty** — no auto-generated README, licence or `.gitignore`. A
      pre-populated remote gives you an unrelated history to reconcile on the very first push,
      and the usual escape from that is a force-push.
- [ ] `git remote -v` — read the URL and confirm it is the account and repository you meant.
- [ ] Confirm the repository's **visibility matches the intent before pushing**, not after.
      Making a repository private later does not un-publish what was already fetched, cached or
      indexed; anything secret in the history must be rotated, not hidden.
- [ ] `git push -u origin <branch>` — set the upstream on the first push so later pushes have a
      default and `@{upstream}` resolves.

Sources: reasoned from first principles, 2026-08-30; `git-push(1)` `-u`/`--set-upstream`,
git 2.x.

## Questions worth asking once it exists

- [ ] Does anything in the first commit contain a value that would need rotating if this
      repository were public tomorrow?
- [ ] Is the default branch protected, or can it be force-pushed by anyone with access?
- [ ] Could someone clone this and build it from the README alone, or only from what is in your
      shell history?

Sources: reasoned from first principles, 2026-08-30.
