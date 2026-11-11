# 0650 — Typed landmark: its 📍 chip, offered as a place, refreshed by undo

- **Priority**: Medium
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/index/spot_rows.py`, `src/media_hygiene/review/templates/`, `src/media_hygiene/slideshow/`, `src/media_hygiene/places/`

## Problem

Rest of 0649 (commit 4a39ad6f, PARTIAL): a landmark typed in the large view (key L) is written to
the sidecar and cached in `spots`, but it is not shown on the tiles, not in the slideshow corner,
not offered as a place, and `mh undo` of it leaves the `spots` row stale.

## Acceptance

- [ ] 📍 chip beside the tags (tile, large view), searchable; the slideshow corner shows it
- [ ] A confirmed name offered as a place (`[[classify.places]]`, circle around it), never silent
- [x] `mh undo` of a landmark run refreshes the `spots` row (test)
- [ ] Headless Chromium check of the dialog (skill `photo-picking-pages`)

## Done (2026-11-07)

- `mh undo` of a landmark run rewrites the `spots` rows of the sidecars it reversed
  (`services/undo_landmarks.py`, called from `undo_index.follow_moves_back`): the sidecar's
  name again, or the user's name dropped (stamp emptied, town kept, next audit names it).
  Test: `tests/integration/tags/test_landmark_sidecars.py` (fails without the hook).
- A typed name is searchable at once: the desk marks the full-text table stale (its own
  writes do not change SQLite's `data_version`).
- Found already there: the tile's and large view's 📍 line and the TV corner read
  `spots.landmark` (0545), so a typed name shows on them once cached.

## Left

- [ ] A 📍 *chip* (clickable, beside the tags) instead of the 📍 line — or decide the line is enough
- [ ] Confirmed name offered as a place (`[[classify.places]]`, circle), never silent
- [ ] Headless Chromium check of the dialog; `docs_screenshots`

## Inbox (2026-11-08)

Stale: the rest (chip, place offer, headless Chromium check) was done by 0651; only `docs_screenshots` remains, a general run. Closed.
