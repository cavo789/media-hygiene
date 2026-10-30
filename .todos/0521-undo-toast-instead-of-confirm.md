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
