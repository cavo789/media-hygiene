# Iterate

Run the open backlog unattended, lot after lot, as `.todos/plan.md` orders it: first unblock what
waits for an answer, then implement each lot **in a subagent**, commit, regenerate the plan, and
keep a feedback file the user reviews afterwards.

**Usage:** `/iterate` — every runnable lot and standalone TODO, in plan order.
`/iterate <n>` — stop after `n` lots or standalone TODOs.

The work on each TODO follows `/todo` (`.claude/commands/todo.md`): readiness, locks,
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
2. Read `.todos/plan.md`. If its counts differ from `.claude/scripts/todo_plan_tables.sh`, the
   plan is stale: regenerate it (`/todo-plan`) first.
3. Create the feedback file `.claude/plans/feedback-<YYYY-MM-DD>-iterate.md` (private,
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
`general-purpose` subagent, in the foreground (the next lot depends on its commit). The prompt
gives it everything it needs, since it starts cold:

- the TODO IDs of the lot, and: "Follow `.claude/commands/todo.md` (Phases 0–5) on them, and
  `.claude/rules/workflow.md`. Run targeted tests while working, then once the lot is complete
  the unit tests and the integration tests, one after the other, gently (`nice`,
  `PYTHON_CPU_COUNT=4`), and the commit gate on the changed files.";
- "A TODO not ready (a question to the user, data you cannot reach): do not ask — skip it, and
  say why in your report.";
- "Append the section of each TODO to `<feedback file>` (template in
  `.claude/commands/iterate.md`).";
- "Then `git fsck --no-dangling` and one commit for the lot: code, tests, docs, translations,
  the moved TODO files and the plan; the message names the TODO IDs and the measured gains.
  Never push, never `git stash`.";
- "Report in at most 15 lines: per TODO the outcome (DONE / PARTIAL / skipped and why), the
  commit hash, the tests run and their result, the gains (before → after, %, measured or
  estimated), the questions for the user. Nothing else: no diff, no logs."

After each subagent:

1. Check its claims cheaply: `git log --oneline -1` (the commit exists), `git status --porcelain`
   (clean tree). A dirty tree or a missing commit: stop and tell the user what the report says.
2. Keep its report (it feeds the final summary) and give the user a one-line progress note.

Stop early when: a lot ends with a failure its subagent could not fix (the tree stays as the
subagent left it, described in the feedback file); the user sends a message (answer it, go on
unless they say stop); `/iterate <n>` reached `n`.

## Phase 3 — End

1. Finish the feedback file: the gains table, the questions, what waits for the user
   (measurements with the exact command, decisions, files to provide).
2. Final message to the user, in their language: the commits (hash, subject), the gains table,
   the questions, what waits for them, the path of the feedback file, the next step from
   `.todos/plan.md`. Then `/todo`'s Phase 6 commit reminder.

## Feedback file template

```markdown
# Feedback — /iterate of <date>

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
