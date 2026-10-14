# Review feedback

Go through the feedback file of an unattended run (`/iterate`, or any run that kept one) with the
user: question by question, apply each decision, file the follow-ups, and close the file.

**Usage:** `/review-feedback` — the most recent `.claude/plans/feedback-*.md`.
`/review-feedback <file>` — that file.

The user may be on a small screen: one decision at a time, short options, the recommended one
first. Speak the user's language.

## Phase 0 — Read

1. Open the feedback file (the newest by modification time when none is given). If it carries a
   `## Reviewed (<date>)` section, say so and ask whether to review it again.
2. List what needs the user, from every TODO section and the closing sections:
   - **Questions** (`**Question**:` bullets, the *Questions* section);
   - **Deviations** from a TODO (`**Deviation**:`): the user accepts or asks to change them;
   - **Waiting for you** (measurements, files, decisions) — not answerable here, only listed.
3. Show a compact overview first: how many questions and deviations, which TODOs and commits they
   concern, what waits for the user. Then start.

## Phase 1 — One decision at a time

For each question or deviation, in the order of the file:

1. Give the context in 2–4 lines: what was done (the commit), what was chosen and the alternative
   left aside, what each answer implies (behaviour, files touched, cost). Read the code or the
   commit only as far as needed to state that accurately.
2. Ask (AskUserQuestion: at most 4 questions per call, related ones together; the recommended
   option first, with "(Recommended)"; "keep as is" is always one of the options).
3. Record the answer in the feedback file next to the question (`→ <answer> (<date>)`).

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

Regenerate the plan (`/todo-plan`) when TODOs were filed, then commit the backlog. Never push
unless asked.

## Phase 3 — Close

1. Append `## Reviewed (<date>)` to the feedback file: the decisions in one line each, the commits
   made, the TODOs filed, what still waits for the user.
2. Final message: the same, short, and the next step (`/iterate` when the plan has runnable lots).
