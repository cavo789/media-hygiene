# 0137 — `review-sort`: load the next event's thumbnails ahead, like `review` does

- **Priority**: Medium — each new event waits for its thumbnails to be decoded on request
- **Batch**: review-sort
- **Depends**: 0133
- **Files**: `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/review/sort_app.py`, `tests/integration/test_sort_review.py`

## Context

Speed review of 2026-10-14. The pages of `review` (`review_board.js.j2`: `new Image().src` for the
next page's shots) and `review --near` (`near_review.js.j2`, the next group) already ask for the
next pictures while the user decides. `review-sort` does not.

`sort_review.html.j2` builds each event's figures with `loading = "lazy"` and `src = photo.thumb`
only when the event is shown. On every event, the server (`sort_app._thumb`, 400 px
`jpeg_preview` in the process pool) has to decode up to the whole event at once while the user
waits. The 1600 px zoom (`photos[cursor].preview`) is not loaded ahead either.

## What to do

1. When an event is shown, request the thumbnails of the next event (and of the previous one when
   going back): `new Image().src = photo.thumb`, as `review_board.js.j2` does.
2. Request the zoom preview of the photo under the cursor and of its two neighbours.
3. Keep it bounded: one event ahead, so a large event does not flood the process pool.
4. With 0133, these requests hit the preview cache from the second session on.

## Acceptance

- Opening the next event shows its thumbnails without waiting: the page asked for them in
  advance. A test of the rendered script checks that the next event's thumbnails are requested.
- No change in the decisions saved (`sort-decisions.json`).
