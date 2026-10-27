# 0420 — search *Why this name?*: the face outlined on the whole photo

- **Priority**: Low
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/people/crops.py`, `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/search.js.j2`

## Why

Leftover of 0318, asked by the maintainer (inbox, 2026-10-27): when the photo holds several faces,
outline the face named on the whole photo, not only the crop.

## What

Send the upright photo's size next to the face's box (`POST /api/people/why`), scale the box on
the preview, draw it (both themes). Skill `photo-picking-pages` for the large view.
