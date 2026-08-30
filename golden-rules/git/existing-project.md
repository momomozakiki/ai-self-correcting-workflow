# Git — golden rules (existing project)

Status: drafted by orchestrator 2026-08-30, unreviewed
Applies when the repo already has commits and a remote. For a repo that does not exist yet,
see `new-project.md`.

## Before touching anything

- [ ] `git fetch --all --prune`
- [ ] `git status --short` — if the tree is dirty, **stop and ask**. Never stash, reset or
      commit someone else's work-in-progress to clear your path.
- [ ] `git branch --show-current` — know where you are before you move.

Sources: Pro Git, 2nd ed. (Chacon & Straub, 2014) ch.2–3.

## Before cutting a branch — verify the base, don't assume it

- [ ] Name the files the work will touch, then confirm they **exist on the intended base**:
      `git ls-tree -d --name-only <base> -- <path> [<path>...]`
- [ ] `git log --oneline <base>..<current> | wc -l` — if the count is not zero, the two
      branches differ; know how before choosing.
- [ ] Choose the base by **where the work's dependencies live**, not by habit. `main` is the
      default, not the answer.
- [ ] If the base turns out to be wrong, re-cut immediately: `git switch <right-base>`,
      `git branch -D <wrong-branch>`, `git switch -c <name>`. Cheap before the first commit,
      expensive after.

Sources: Incident 2026-08-29 — a branch was cut from `main` for a migration whose every target
file (`.ai/`, `.claude/agents/`, `.claude/skills/`, `.claude/rules/`, `templates/ai-library/`,
three of four test files) existed only on the feature branch 25 commits ahead. Caught on the
first `cat` of a file the plan named, before anything was written. Nothing verified that the
base contained the subject of the work, because nobody thought to ask.

## While working

- [ ] Branch name says what the work is: `<type>/<slug>`. Never commit directly to the default
      branch.
- [ ] Commit when a change is coherent, not when a file is saved.
- [ ] Before `git add -A`, check what it would sweep in: `git status --short`. Transient
      session state that lives in the working tree is the usual casualty.

Sources: Pro Git, 2nd ed. (2014) ch.3; Conventional Commits 1.0.0.

## Writing the commit

- [ ] `git commit -m` (repeatable for multiple paragraphs) or `-F <file>`.
- [ ] **Never** `-F -`, a heredoc, or a bare `git commit`. Escapes mangle silently and a
      bare invocation opens an editor that cannot be driven.
- [ ] The message says **why**, not what — the diff already says what.

Sources: Incident 2026-08-04 (recurring, ×2 — the first was `git commit -F -` and heredoc
commit messages) — heredoc stdin mangled content without error; `docs/RETROSPECTIVE.md`,
codified in `.claude/rules/repo-conventions.md`.

## Before pushing

- [ ] Re-run the project's test command; a green suite locally is the minimum.
- [ ] `git log --oneline origin/<branch>..HEAD` — read what you are about to publish.
- [ ] Push with upstream on first push: `git push -u origin <branch>`.
- [ ] **Never** force-push a shared branch. Never rewrite published history.

Sources: Pro Git, 2nd ed. (2014) ch.3; GitHub Flow (github.com/github/docs, retrieved
2026-08-29).

## Questions worth asking before you call it done

- [ ] If someone pulled this branch and ran nothing, would they be misled about its state?
- [ ] Is anything staged that is machine-generated and rewritten on every run?
- [ ] Does the branch still target the base it was cut from, or has the work drifted somewhere
      else?

Sources: reasoned from first principles, 2026-08-29.
