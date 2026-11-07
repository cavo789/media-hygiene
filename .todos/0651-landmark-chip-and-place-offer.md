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

- [ ] 📍 chip among the tags (tile, large view); a click shows every photo of that landmark
- [ ] A confirmed name offered as a place (circle around it), asked, never silent
- [ ] Headless Chromium check of the landmark dialog and the chip (skill `photo-picking-pages`)
