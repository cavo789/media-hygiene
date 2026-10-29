# 0461 — Family home page: *On this day*, *Latest additions*, *Slideshow on the TV*, *Map*, `[home] family_title` (rest of 0293)

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/home_draw.js.j2`, `src/media_hygiene/review/home_texts_family.py`, `src/media_hygiene/config/`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Why

0293 (closed) built the family view of a paired phone; its decisions of 2026-10-23 still to build:
all four entrances and the title setting.

## What

- *On this day*: photos of today's month-day in earlier years (a query over the index, an API in
  the phone's list, thumbnails).
- *Latest additions*, *Slideshow on the TV*, *Map* entrances.
- `[home] family_title`, empty by default ("Our photos" / "Nos photos"); never a name in the repo.

## Acceptance

A paired phone sees today's memories from the index; every figure comes from the index; no
external resource, no endless animation. Docs en + fr.
