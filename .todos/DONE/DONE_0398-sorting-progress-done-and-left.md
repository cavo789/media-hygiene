# 0398 — Sorting little by little: what is done, what is left, how it moves on

- **Priority**: Medium
- **Batch**: review-sort
- **Depends**: 0397
- **Files**: `src/media_hygiene/review/sort_progress.py`, `src/media_hygiene/review/sort_session.py`, `src/media_hygiene/review/sort_state.py`, `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/actions/sort_resume.py`, `src/media_hygiene/review/home_views.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`

## Why

Maintainer, 2026-10-25: "since I will sort little by little (one event at a time), how am I
told what was done and what is left? I would like to follow the progress." He thought of
moving everything first into a `To sort` folder, so that the progress is seen as it empties,
and doubted it is clean. It is not: every photo would move twice, his own structure would be
broken before anything is decided, the undo history doubled. The tool knows the progress
already: the journal holds the rows each `sort` run moved (`actions/sort_resume.moved_targets`),
the plan which files already sit where it puts them (`PlanRow.in_place`).

## What

- A **progress line** on the review-sort page, in the bar or above the event list: "Sorted:
  23 events, 1,840 files (3.5 %) · already in place: 35,000 files · left: 1,114 events,
  15,216 files to move", from the plan and the journal (rows moved by any run of the plan, not
  undone; rows already in place), read again after each GO (0397).
- Each event carries its state: **sorted** (its files moved, 0390), **in place** (nothing to
  move), **chosen, not sorted yet**, **to decide**; a filter *Only the events not sorted yet*
  beside the two of 0388 (one at a time), and U goes to the next one not sorted.
- A short **history of this plan's runs** in the left column, latest first: "25/10 14:32 ·
  Mariage d'Hervé et Magda · 14 files · undo 20261025-143212" (the runs of the journal for this
  plan, `history` read), each with its undo line.
- On the home page, the sorting space shows the same figures (sorted / in place / left) for
  the latest classify run.
- No staging folder: nothing is moved to follow the progress.

## Tests

The counts against a plan with rows moved by two runs, one undone; an event fully moved shows
*sorted*, one in place *in place*; the filter's walk; the history lists the runs of the plan
only, latest first.
