# Reviewed feedback files move to .claude/plans/reviewed/

- **Priority**: Medium
- **Batch**: claude-tooling
- **Depends**: —
- **Files**: `.claude/scripts/feedback_pending.py`, `.claude/scripts/todo_inbox.py`, `.claude/commands/todo/review-feedback.md`

## Context

`feedback_pending.py` and `todo_inbox.py` (`feedback()`, line ~131) open every
`.claude/plans/feedback-*.md` to look for `## Reviewed`: the cost grows with every run ever made.

## Change

- The location is the state: pending = `glob("feedback-*.md")` at the top of `.claude/plans/`,
  nothing else read.
- `feedback_pending.py done FILE [--note TEXT]`: appends `## Reviewed (<date>)` (+ the note), then
  moves the file to `.claude/plans/reviewed/`. `/todo:review-feedback` calls it when it closes a
  file — never a move by hand.
- One-off migration: move every file already carrying `## Reviewed`.
- Tests of the script (pending listing ignores `reviewed/`; `done` appends and moves).
