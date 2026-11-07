# 0651 — Typed landmark: a clickable 📍 chip among the tags, and offered as a place

- **Priority**: Low — few photos of the collection carry GPS (281 located photos measured in 0489; the maintainer confirms most have none)
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/`, `src/media_hygiene/search/`, `src/media_hygiene/places/`

## Problem

Rest of 0650 (commit 7761e89e, PARTIAL) and 0649 (commit 4a39ad6f). A typed landmark shows on a 📍
line (tile, large view, slideshow corner) but is not a chip one can click, and a confirmed name is
not offered as a place (`[[classify.places]]`): no route links `library` to the place writer.

## Decided (2026-11-07, maintainer, review of the iterate of 2026-11-07 (2))

A clickable 📍 chip beside the tags: one click searches that landmark. Rejected names stay in the
photo's sidecar; the 500 m radius stays a constant.

## Acceptance

- [x] 📍 chip among the tags (tile, large view); a click shows every photo of that landmark
- [x] A confirmed name offered as a place (circle around it), asked, never silent
- [x] Headless Chromium check of the landmark dialog and the chip (skill `photo-picking-pages`)

## Status — DONE (2026-11-07)

- 📍 chip first among the words (tile and large view, `search.js.j2` `landmarkChip`): click
  searches the landmark, Ctrl+click adds it; the hit carries `landmark` (`spot_label`).
- After *Write this name*, the dialog asks *A place of yours?*; *Add it as a place* posts
  `action: place` (`search/landmark_place.py`): a 200 m circle around the photo in
  `[[classify.places]]`, read back; a place of that name is kept.
- Headless Chromium (mocked API): chip click searches "Tour Eiffel", nothing picked; L, write,
  offer shown, Yes posts `place`, dialog closes, line shown; no page error of this change.
