# 0601 — A page runs `mh undo <run>` itself: Undo toast on move to an event and Apply now

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: 0521 (PARTIAL)
- **Files**: `src/media_hygiene/review/shared_routes.py`, `src/media_hygiene/services/undo_run.py`

## Why (review of feedback-2026-11-03-iterate (2026-11-05))

0521 left two window.confirm calls (move to an event, Apply now) because no page can undo a run. Decided: add a JSON-only POST route that runs the journaled undo of the run the page just made, then show the shared Undo toast on both actions and drop their confirm. Prove the undo by reading the files back.
