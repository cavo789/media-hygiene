# Iterate

Run the open backlog unattended, lot after lot, as `.todos/plan.md` orders it: first unblock what
waits for an answer, then implement each lot **in a subagent**, on a work branch, one commit per
lot pushed as it goes; at the end a **pull request** whose description is the review: the user
reads it, comments and merges from a phone, and GitHub's CI runs the full suite and the image
end-to-end tests instead of the user's PC.

**Usage:** `/todo:iterate` — every runnable lot and standalone TODO, in plan order.
`/todo:iterate <n>` — stop after `n` lots or standalone TODOs.

The work on each TODO follows `/todo:run` (`.claude/commands/todo/run.md`): readiness, locks,
implementation rules, close-out (DONE / PARTIAL / BLOCKED), plan refresh. The working method of
`.claude/rules/workflow.md` applies throughout. This command adds the orchestration: what to ask
first, what to delegate, what to commit, what to report.

## Why subagents

A lot reads and edits dozens of files and runs long test outputs; done in the main session, every
later lot re-sends all of it. Each lot runs in its own subagent: the main session keeps only a
short report per lot, so a run of ten lots costs about as much context as one.

## Phase 0 — Start

1. `git status --porcelain`: a dirty tree means another session (or the user) is working — stop
   and ask. Never `git stash`.
2. Regenerate `.todos/plan.md` (`python3 .claude/scripts/todo_plan_render.py .todos`), then read it.
3. Create the work branch `iterate/<YYYY-MM-DD>` from an up-to-date `main` (`git switch -c`; a
   second run the same day: `-2`, `-3`). Never commit a `/todo:iterate` run on `main`: a push of
   `main` rebuilds the published image; the user merges the pull request when satisfied.
4. Create the feedback file `.claude/plans/feedback-<YYYY-MM-DD>-iterate.md` (private,
   git-ignored) from the template below; tell the user its path in one line.

## Phase 1 — Unblock first (while the user is here)

Blocked TODOs never enter the queue: they would only end PARTIAL for want of an answer. Collect
what blocks, cheaply (no implementation, headers and the questions only):

- the TODOs listed under *Waiting for the maintainer* (`Needs maintainer`), with what they need;
- in the TODOs of the queue, an explicit question to the user ("the maintainer confirms or drops
  it", "decision", "open question", an `Options` section to choose from).

Then **offer to answer them now**, before any implementation (AskUserQuestion, at most 4 questions
per call, the recommended option first, each option saying what it implies). For each answer:

- write it into the TODO (a `## Decided (<date>)` section: the choice, by whom), and remove its
  `Needs maintainer` bullet when nothing else is needed: it joins the queue;
- a need that is not an answer (a measurement on the user's machine, real files, an account)
  cannot be given here: say so, leave the TODO waiting.

The user may decline or skip: those TODOs stay out of the queue, listed in the feedback file
under *Waiting for you*. If the user is not there (the run was started to go unattended), skip
this phase and leave every blocked TODO out.

Commit the decided TODOs (`Backlog: decisions for …`), regenerate the plan, then build the
queue: the *Recommended order* lots, then *Standalone* by priority; never a TODO still waiting
or locked.

## Phase 2 — One lot at a time, each in a subagent

Lots run **one after the other** (they share the working tree), each delegated to a
`general-purpose` subagent, in the foreground (the next lot depends on its commit).

**Model per lot** (the `model` parameter): run `python3 .claude/scripts/todo_model.py NNNN` on
each TODO of the lot (when the project has it); `sonnet` only when every TODO of the lot says
`sonnet`, else `opus`. The script's rules: `opus` for anything touching the user's files or what
protects them, caches, concurrency, an open question, a past mistake, many source files, and in
doubt; `sonnet` for text only (docs, translations, backlog) or small Low work. Without the
script, the same rules by hand. Say the choice and its reason in the progress line.

The prompt gives the subagent everything it needs, since it starts cold:

- the TODO IDs of the lot, and: "Follow `.claude/commands/todo/run.md` (Phases 0–5) on them, and
  `.claude/rules/workflow.md`. Run the targeted tests of what you touch and the commit gate on the
  changed files; the full suite and the image tests run in CI on the pull request, not here (the
  user's PC suffers under heavy load). Run the whole unit suite (fast) once before committing.";
- "A TODO not ready (a question to the user, data you cannot reach): do not ask — skip it, and
  say why in your report.";
- "Append the section of each TODO to `<feedback file>` (template in
  `.claude/commands/todo/iterate.md`).";
- "Then `git fsck --no-dangling`, one commit for the lot on the current branch (code, tests,
  docs, translations, the moved TODO files and the plan; the message names the TODO IDs and the
  measured gains), and `git push -u origin HEAD`. Never push `main`, never `git stash`.";
- "Report in at most 15 lines: per TODO the outcome (DONE / PARTIAL / skipped and why), the
  commit hash, the tests run and their result, the gains (before → after, %, measured or
  estimated), the questions for the user. Nothing else: no diff, no logs."

After each subagent:

1. Check its claims cheaply: `git log --oneline -1` (the commit exists), `git status --porcelain`
   (clean tree), the branch pushed. A dirty tree or a missing commit: stop, notify the user
   (below), and tell what the report says.
2. Keep its report (it feeds the final summary) and give the user a one-line progress note.

Stop early when: a lot ends with a failure its subagent could not fix (the tree stays as the
subagent left it, described in the feedback file); the user sends a message (answer it, go on
unless they say stop); `/todo:iterate <n>` reached `n`.

## Phase 3 — End

1. Finish the feedback file: the gains table, the questions, what waits for the user
   (measurements with the exact command, decisions, files to provide).
2. Open the pull request (`gh pr create --base main --head <branch>`), in the user's language:
   title `Iterate <date>: <TODO IDs>`; body = the review — per TODO (outcome, commit, gain), the
   gains table, the **questions as a numbered list** (the user answers in comments: "2: keep",
   "3: setting please"), what waits for them, and the next step. The repository is public: no
   personal data in it (no private paths, names, figures of the user's own library beyond what
   the TODOs already publish); the full details stay in the private feedback file.
3. Watch the CI of the pull request in the background (`gh pr checks <n> --watch`, run in the
   background; never a foreground wait). A failure: read its log (`gh run view --log-failed`),
   fix it on the branch in a subagent, push again.
4. **Notify the user** (`PushNotification`, one short line) at the end — pull request opened, CI
   green or red — and whenever the run stops early or waits for them. They may be away from the
   terminal.
5. Final message to the user, in their language: the pull request link, the commits, the gains
   table, the questions, what waits for them, the next step (`/todo:review-feedback`, then merge).
   Never merge it yourself.

## Feedback file template

```markdown
# Feedback — /todo:iterate of <date>

Private notes for the review: per TODO the questions met, the choices made (and the alternatives
left aside), deviations from the TODO, what could not be checked here, what waits for the user.

Decided at the start: <TODO: answer, one line each>. Queue: <lots and standalone TODOs, in
order>. Commits on <branch>, not pushed.

---

## <NNNN> — <title>

- **Choice**: <what was decided, and the alternative left aside, why>
- **Deviation**: <where the work differs from the TODO, and what showed it (a test, a measure)>
- **Gain**: <before → after, %, measured (how) or estimated (from what)>
- **Question**: <what the user should decide or confirm>
- **Not done**: <what remains, why; the exact command for a measurement only the user can run>

---

## Gains

| Where | Before → after | Gain |
|---|---|---|

## Questions

## Waiting for you
```
