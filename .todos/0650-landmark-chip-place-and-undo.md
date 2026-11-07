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
- [ ] `mh undo` of a landmark run refreshes the `spots` row (test)
- [ ] Headless Chromium check of the dialog (skill `photo-picking-pages`)
