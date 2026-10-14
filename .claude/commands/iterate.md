# Iterate

Run the open backlog unattended, lot after lot, as `.todos/plan.md` orders it: implement, verify,
commit, regenerate the plan, and keep a feedback file the user reviews afterwards.

**Usage:** `/iterate` — every runnable lot and standalone TODO, in plan order.
`/iterate <n>` — stop after `n` lots or standalone TODOs.

This command **orchestrates**; the work on each TODO follows `/todo` (`.claude/commands/todo.md`):
its readiness check, locks, implementation rules, close-out (DONE / PARTIAL / BLOCKED) and plan
refresh apply unchanged. Read it first. The working method of `.claude/rules/workflow.md` applies
throughout (commit gate, measured vs estimated, gains, unattended runs).

## Phase 0 — Start

1. `git status --porcelain`: a dirty tree means another session (or the user) is working — stop
   and ask. Never `git stash`.
2. Read `.todos/plan.md`. If its counts differ from `.claude/scripts/todo_plan_tables.sh`, the
   plan is stale: regenerate it (`/todo-plan`) before going on.
3. The queue, in this order: the *Recommended order* lots, then *Standalone* by priority. Never
   take a TODO listed under *Waiting for the maintainer* (`Needs maintainer`) or *Currently in
   progress* (locked).
4. Create the feedback file `.claude/plans/feedback-<YYYY-MM-DD>-iterate.md` (private,
   git-ignored) from the template below, and tell the user its path in one line.

## Phase 1 — One lot at a time

For each lot (or standalone TODO) of the queue:

1. Run the `/todo` procedure on its IDs. A TODO found not ready (a blocker `/todo` Phase 1 would
   ask about) is **skipped**, not asked: write the blocker in the feedback file and go on with the
   rest of the lot.
2. Verify: targeted tests while working; once the lot is complete, the unit tests then the
   integration tests of the project, one after the other, gently (`.claude/rules/workflow.md`,
   project facts); the commit gate on the changed files.
3. Close out each TODO as `/todo` Phase 3 says. A TODO whose only remaining item is a
   measurement or a decision of the user ends PARTIAL, with that item in `### Not done`.
4. Refresh `.todos/plan.md` (`/todo` Phase 5; counts and PARTIAL table from
   `todo_plan_tables.sh`).
5. `git fsck --no-dangling`, then **one commit for the lot**: code, tests, docs, translations,
   the moved TODO files and the plan, message naming the TODO IDs and the measured gains.
   **Never push** unless the user asked.
6. Append the lot's section to the feedback file (template below).
7. Give the user a one-line progress note (lot done, commit, next lot).

Stop early when: a test failure cannot be fixed within the TODO's scope (leave the tree clean:
commit what is green, describe the rest in the feedback file); the user sends a message (answer
it, then go on unless they say stop); `/iterate <n>` reached `n`.

## Phase 2 — End

1. Finish the feedback file: the gains table (where, before → after, %, measured or estimated),
   the questions for the user, what waits for them (measurements with the exact command, decisions,
   files to provide).
2. Final message to the user, in their language: the commits (hash, subject), the gains table,
   the questions, what waits for them, the path of the feedback file, the next step from
   `.todos/plan.md`. Then `/todo`'s Phase 6 commit reminder.

## Feedback file template

```markdown
# Feedback — /iterate of <date>

Private notes for the review: per TODO the questions met, the choices made (and the alternatives
left aside), deviations from the TODO, what could not be checked here, what waits for the user.

Queue at the start: <lots and standalone TODOs, in order>. Commits on <branch>, not pushed.

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
