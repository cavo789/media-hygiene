# 0621 — ↶ Undo after Apply now on the review and faces pages too

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: 0601 (PARTIAL)
- **Files**: `src/media_hygiene/review/shared_routes.py`, `src/media_hygiene/people/`

## Why

Review of 0601: `/api/undo-run` is served by the Library page only; the review pages and the faces page still have no Undo after *Apply now*.

## What

Serve the route on every page that offers *Apply now*, and show the same Undo toast there.

## Done when

Every Apply now page offers Undo of the run it just made, disk checked after (tests).
