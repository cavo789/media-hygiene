# Review feedback

Go through the feedback file of an unattended run (`/todo:iterate`, or any run that kept one) with the
user: question by question, apply each decision, file the follow-ups, and close the file.

**Usage:** `/todo:review-feedback` — **every** `.claude/plans/feedback-*.md` not reviewed yet,
oldest first, and the open pull request of each `/todo:iterate` branch when there is one.
`/todo:review-feedback <file>` — that file only.

Why all of them: the user cannot know which files are left. Taking only the newest once hid a
file for two weeks (a manual run's feedback, overtaken by later runs before any review).

The user may be on a small screen: one decision at a time, short options, the recommended one
first. Speak the user's language.

## Phase 0 — Read

1. Take the inventory: `python3 .claude/scripts/feedback_pending.py` lists every feedback file
   without a `## Reviewed (<date>)` heading, oldest first, with its count of questions and
   deviations (the heading Phase 3 writes is the record: no list to keep by hand). Say in one
   line how many are pending; none → say so and stop. A file given as argument is reviewed even
   when it carries the heading (ask first whether to review it again).
   Then go through the pending files one after the other, oldest first: Phases 0–3 for each
   (its own `## Reviewed` heading at its close, so an interrupted session resumes at the next).
   An old file: check each item against today's code and backlog first; an item done or
   superseded since is closed as *stale* in one line, never asked.
2. List what needs the user, from every TODO section and the closing sections:
   - **Questions** (`**Question**:` bullets, the *Questions* section);
   - **Deviations** from a TODO (`**Deviation**:`): the user accepts or asks to change them;
   - **Waiting for you** (measurements, files, decisions) — not answerable here, only listed.
3. When a `/todo:iterate` pull request exists (`gh pr list --head iterate/…`), read its comments
   (`gh pr view <n> --comments`, and the review comments with `gh api
   repos/{owner}/{repo}/pulls/<n>/comments`): an answer given there ("2: keep", a remark on a
   line) is taken as the answer to that question; confirm it in one line instead of asking again.
4. Show a compact overview first: how many questions and deviations, which TODOs and commits they
   concern, what waits for the user. Then start.

## Phase 1 — One decision at a time

For each question or deviation, in the order of the file:

1. Never a bare ID: name each TODO by what it is for the user ("0480 **la chaîne après un
   import téléphone**"), in the context and in the question text itself — the user does not
   remember IDs and often reads on a phone.
2. Give the context in 2–4 lines: what was done (the commit), what was chosen and the alternative
   left aside, what each answer implies (behaviour, files touched, cost). Read the code or the
   commit only as far as needed to state that accurately.
3. Ask (AskUserQuestion: at most 4 questions per call, related ones together; the recommended
   option first, with "(Recommended)"; "keep as is" is always one of the options).
4. Record the answer in the feedback file next to the question (`→ <answer> (<date>)`).

## Phase 2 — Apply

Group the answers by what they lead to:

- **Keep as is** — nothing to do.
- **A small change** (a constant, a wording, a default, a test): do it now, following
  `.claude/rules/workflow.md` (commit gate, targeted tests, docs en + fr when user-facing), one
  commit per decision group, message naming the TODO IDs and "review of <feedback file date>".
- **A larger change, or one needing a measurement** — file a TODO (skill `todo-authoring`; a
  `Needs maintainer` bullet when it waits for the user), referencing the TODO and commit it
  follows. A PARTIAL TODO whose remaining item is now decided: file the remainder as a fresh TODO.
- **A rule for next time** (a pattern the user corrected) — add it to `.claude/rules/workflow.md`
  or the project rules, short; a personal preference goes to memory instead.

Regenerate the plan (`/todo:plan`) when TODOs were filed, then commit the backlog — on the
`/todo:iterate` branch when the run has one (push it: the pull request follows), else as the user
asks. Never merge the pull request: the user does, once satisfied.

## Phase 3 — Close

1. Answer the pull request comments in one line each (what was done, the commit), so the thread
   reads as closed on the phone.
2. Append `## Reviewed (<date>)` to the feedback file: the decisions in one line each, the commits
   made, the TODOs filed, what still waits for the user.
3. Final message: the same, short, and the next step (merge the pull request; `/todo:iterate` when
   the plan has runnable lots).
