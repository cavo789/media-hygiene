# 0601 — A page runs `mh undo <run>` itself: Undo toast on move to an event and Apply now

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: 0521 (PARTIAL)
- **Files**: `src/media_hygiene/review/shared_routes.py`, `src/media_hygiene/services/undo_run.py`

## Why (review of feedback-2026-11-03-iterate (2026-11-05))

0521 left two window.confirm calls (move to an event, Apply now) because no page can undo a run. Decided: add a JSON-only POST route that runs the journaled undo of the run the page just made, then show the shared Undo toast on both actions and drop their confirm. Prove the undo by reading the files back.

## Status — PARTIAL (2026-11-05)

### Done
- `GET`/`POST /api/undo-run` (`search/undo_api.py`, `services/page_undo.py`): undoes the
  journal's latest run only (an older one: 409 naming `mh undo <run>`), then looks for each
  file where it was; the answer counts the files found back (`back` of `meant`). PC-only
  (`write_routes.CHANGES`). Test: `tests/integration/test_page_undo.py` (a real clean on the
  demo tree, undone from the route, disk identical afterwards).
- Move to an event (`search_rule.js.j2`): `window.confirm` removed; the shared Undo toast
  after the move, its Undo runs the route and re-reads the tiles.
- *Apply now* (`apply_now.html.j2`) on the search/browse page: the latest run seen before the
  click is kept; once the step ended, a newer run gets the Undo toast. `mhUndoRun` lives in
  `undo_toast.html.j2`. Run in headless Chromium (mocked server): apply → step → toast → undo.

### Not done
- *Apply now* of the review pages, the people page and the other pages: their servers do not
  answer `/api/undo-run` (`undo_path` unset), so no toast there.
  **Reason:** the route needs a `Runtime`; `shared_routes.asset_or_page` has none. Give
  `EndingDoor`/`ReviewHere` a `PageUndo` (or the home server one router-level route) next.
- *Apply now* in its "applying" mode (the server ends, the home page opens): no toast.
  **Reason:** the page is left; the home page would have to offer it.
