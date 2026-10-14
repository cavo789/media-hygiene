# TODO inbox

Everything the backlog waits for from the maintainer, in one place: answer what can be answered
in a chat, now, a few questions at a time; group what needs their machine into one action; then
apply the answers (close, refile, unblock) so the backlog moves again.

**Usage:** `/todo:inbox` — the whole backlog. `/todo:inbox 0150 0145` — only those TODOs.

Why it exists: the maintainer's answers, not the code, became the bottleneck. A PARTIAL file
waiting for one "keep the default" costs a re-read of the file every time the plan is shown.

The maintainer may be on a phone: short questions, the recommended option first, the default
(what the code does today) always one of the options. Speak the maintainer's language.

## Phase 0 — Collect

1. Run `python3 .claude/scripts/todo_inbox.py` (pass `.todos` and the project's measure script
   when they differ from the defaults). It prints one record per item: the TODO, its state, the
   item and its reason, the open TODOs it unblocks, whether the measure script covers it.
2. Read each record's file as far as needed to state the item accurately (the context, what
   was done, the default). Do not trust the first line of an item alone.
3. Sort every item into exactly one bucket:
   - **Answer now** — a decision, a confirmation, a go-ahead, a wording: answerable from what
     Claude can show in the chat.
   - **Measure** — covered by the measure script (`MEASURED-BY: yes`, or its header names the
     TODO): one action for all of them, "run the script, then tell Claude".
   - **Material** — needs something only the maintainer has (real files, an account, a device):
     say what, exactly, and where to put it.
   - **Measure, not covered yet** — a measurement the script lacks: propose adding a step to the
     script (`.claude/rules/workflow.md`: never a list of commands to type).
   - **Stale** — no longer true (done since, superseded, its reason gone): propose to close it.
   - **Feedback file** — an unattended run not reviewed yet: point at `/todo:review-feedback`.
4. Show the overview first, short: how many items per bucket, and for **Answer now** the order
   (most open TODOs unblocked first, then High before Low). Then start.

## Phase 1 — Ask (Answer now, then Stale)

- AskUserQuestion, at most 4 related questions per call. Each: 2–3 lines of context (what the
  code does today, what the alternative changes and costs), then the options: the recommended
  one first with "(Recommended)", "Keep the default" always present, "Later" when the
  maintainer cannot judge from the chat (it stays in the inbox).
- A choice of design the maintainer made earlier (`.claude/rules/workflow.md`): list what the
  change loses before asking.
- Record each answer at once in the TODO file, next to the item (`→ <answer> (<date>)`), so an
  interrupted session loses nothing.

## Phase 2 — Apply

Per TODO, once every item of it is answered:

- **Open TODO** whose `Needs maintainer` is answered: write the decision into the body, remove
  the `Needs maintainer` bullet: it becomes runnable by `/todo:run` and `/todo:iterate`.
- **PARTIAL / BLOCKED** where every remaining item is "keep" or "stale": `git mv` to `DONE/`
  (work done, rest dropped) or `UNNEEDED/` (nothing of it is wanted any more), the answers kept
  in its `## Status`.
- **An answer that asks for work**: file a fresh TODO (skill `todo-authoring`), referencing the
  one it follows; `/todo:run` never reaches PARTIAL files. Then close the old one as above.
- **Measure** items: nothing to apply until the results come back; when they do, read the
  results file, then treat each measured item as answered.
- A pattern the maintainer corrected: a short rule in `.claude/rules/workflow.md` (public, no
  personal data) or a memory note when it is a personal preference.

Then regenerate the plan (`python3 .claude/scripts/todo_plan_render.py .todos`), run the commit
gate on the backlog files, and commit by path (`Backlog: inbox of <date> — …`, the IDs closed,
filed and unblocked). Push only when asked.

## Phase 3 — Close

One short message: what was closed, filed and unblocked (IDs), what waits for the measure script
(one line: the command to run), what waits for material, and the next prompt (`/todo:iterate` when
the plan has runnable work, else the measure script).
