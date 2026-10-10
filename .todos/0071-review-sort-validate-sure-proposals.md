# 0071 — review-sort: validate the sure proposals in one batch

- **Priority**: Medium
- **Batch**: review-sort
- **Depends**: 0066
- **Files**: `src/media_hygiene/review/sort_app.py`, `src/media_hygiene/review/sort_session.py`, `src/media_hygiene/review/sort_choices.py`, `src/media_hygiene/review/templates/sort_review.html.j2`, `documentation/en/sort/10-name-events-in-the-browser.md`, `documentation/fr/sort/10-name-events-in-the-browser.md`

## Context

Filed from the 2026-10-10 usability review. `review-sort` shows the events of a classify
plan one at a time; on a large collection most proposals come from a strong rule (high
band) and only need a glance. Check first whether a batch validation already exists in
`sort_review` (none seen during the review).

## Proposal

- Same mechanics as the burst batch (0066): "Accept the N events whose proposal is sure"
  (high band), confirmation with the figures, one undo for the batch; a filter "Only the
  events to decide".
- Sorting stays user-guided: nothing is imposed, the batch only records the proposals the
  user accepts, with their `base` like any other choice; later workbook edits still
  conflict, never settle silently.

## Acceptance

- One write of `sort-decisions.json`, read back from disk; tests; docs en/fr.
