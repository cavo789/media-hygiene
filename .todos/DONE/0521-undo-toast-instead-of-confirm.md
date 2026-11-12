# 0521 — A reversible choice asks nothing: an "Undo" toast replaces window.confirm

- **Priority**: High
- **Batch**: page-shell
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/review_choices.js.j2`, `src/media_hygiene/review/templates/review_obvious.js.j2`, `src/media_hygiene/review/templates/near_review.js.j2`, `src/media_hygiene/search/templates/search_rule.js.j2`, `src/media_hygiene/review/templates/` (shared toast template), `src/media_hygiene/review/apply_api.py`

## Asked (maintainer, 2026-10-30)

"When I set aside and press Apply, I always answered yes: it is exactly what was asked."

## What

- Remove the `window.confirm` of every **reversible** action: setting aside, validating
  series, *Apply now* (quarantine moves, `mh undo` takes them back), moving to an event.
  Found by `grep -rn "confirm(" src/media_hygiene --include=*.j2` (measured 2026-10-30: 10 calls).
- In its place a shared toast "12 photos set aside — Undo" for ~8 s (constant), Z doing the same.
  After *Apply now*, the toast's Undo runs the undo of that run (the page already knows the run).
- Keep a confirmation only where nothing takes it back: `purge`, deleting an album
  (`album.js.j2`, to check whether it is reversible), leaving a page with unsaved choices
  (`events_choice.js.j2`).
- The phone page stays read-only (phone rule): no change there beyond what exists.

## Done when

No `window.confirm` remains on a reversible action (test listing the allowed ones), the toast is
one shared template, and its Undo is proven by reading the decisions file / journal back.

## Status — PARTIAL (2026-11-03)

### Done
- Shared toast `review/templates/undo_toast.html.j2` (`window.mhUndoToast(text, undo, {keys})`,
  `UNDO_TOAST_MS = 8000`, ↶ Undo button, Z when the page's own Z does not already undo).
- No `window.confirm` any more on: validating a folder's series (`review_choices.js.j2`), the
  obvious series (`review_obvious.js.j2`), a near-duplicate folder pair as planned
  (`near_review.js.j2`, G). Their Undo writes `decisions.json` again through the page's usual
  route, which reads the file back (the review's history / `decide(ranks, null)`).
- `tests/unit/test_undo_toast.py` lists every confirmation left, with why.

### Not done
- Moving files to an event (`search_rule.js.j2` goAsk) and *Apply now*: the toast's Undo
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  would have to run `mh undo <run>` from the page; no such route exists yet.
  **Reason:** needs a POST undo route on the search/home server (journal undo of one run),
  its own TODO-sized work.
- Places (a place given photos, a place deleted) and albums (deleted, a photo taken out):
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  config.toml / albums.json edits whose Undo needs the previous content kept and re-sent.
  **Reason:** reversibility to check and an undo per page to write; kept confirmed meanwhile.
- `apply_now.html.j2` itself never used `confirm` (mh asks in its terminal): nothing to remove.
  → nothing left to do: a decision already taken, kept as is (2026-11-12)

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
