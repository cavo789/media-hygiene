# 0527 — Review pages: the biggest gain first

- **Priority**: High
- **Batch**: review
- **Depends**: —
- **Files**: `src/media_hygiene/services/reviewing.py`, `src/media_hygiene/services/near_reviewing.py`, `src/media_hygiene/services/pairs_reviewing.py`, `src/media_hygiene/review/templates/`

## Asked (maintainer, 2026-10-30)

UX brainstorm: order the review by the space it frees, so a huge library gets most of the gain in the first
screens.

## What

- On the bursts, near-duplicate and folder-pair pages: an order "Biggest gain first" (bytes
  the proposal sets aside, descending), beside the current order; the choice remembered by
  the browser (`localStorage`, per-viewer convenience).
- The bar shows the share of the total gain already seen ("62 % of the 40 GB seen").
- Default order: to decide at implementation (say it in the feedback); estimated: the gain is
  concentrated in videos and RAW, so the first screens weigh most.

## Done when

The order is offered on the three pages, ties broken by name (test with the demo tree's
copies), and the share seen is right (test).
