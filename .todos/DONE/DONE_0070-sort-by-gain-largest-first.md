# 0070 — Sort by gain: the largest files first, with the running total

- **Priority**: Medium
- **Batch**: near
- **Depends**: 0069
- **Files**: `src/media_hygiene/report/similar_views.py`, `src/media_hygiene/report/video_views.py`, `src/media_hygiene/report/templates/`, `src/media_hygiene/review/templates/review_order.js.j2`

## Context

Filed from the 2026-10-10 usability review. A few re-encoded videos often weigh more than
hundreds of shrunk photos. A user short of time should get most of the space back in
minutes.

## Proposal

- An order "space freed, largest first" for near duplicates, re-encoded videos (report and
  browser view of 0069) and burst series (page order list).
- A running total: `these 25 groups = 90 % of the space`.

## Acceptance

- Report and page offer the order; unit test on the running total; docs en/fr.
