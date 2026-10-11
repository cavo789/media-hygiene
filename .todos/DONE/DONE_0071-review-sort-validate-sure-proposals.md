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

## Status

DONE (2026-10-11, night run). No batch existed in `review-sort` before.

- `review/sort_sure.py`: an event's proposal is **sure** when the folder most of its files get
  is in the sure band, with a category, some files are still to decide and none of those
  proposes another category; `EventCard.sure` carries it to the page.
- `review/sort_batch.py`: `SortBatchSession` (subclass of `SortSession`) — `POST /api/sure`
  `{events, undo}` accepts the open sure events (value = what Enter records: the proposed
  category, no name; `base` = the workbook's value, empty) or takes back those still holding
  the batch's value, in **one write**, then reads `sort-decisions.json` back from the disk and
  refuses an answer the disk does not hold.
- Page (`templates/sort_review_sure.js.j2`): button + `V` with a confirmation giving the
  figures, `↶ Take the batch back` button, filter "Only the events to decide" (N, P, U skip
  chosen and sure events), `✔ sure` mark after the proposal.
- Console at start: `412 events to decide: 260 with a sure proposal (one click), 152 to look at.`
- Docs en/fr `sort/10-name-events-in-the-browser.md`; tests `tests/unit/test_sort_sure.py`.
- Not run in a real browser (no JS runtime in the night run).
