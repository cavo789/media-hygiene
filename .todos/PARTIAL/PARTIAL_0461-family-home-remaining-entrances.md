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

## Status — PARTIAL (2026-11-03)

Done: `[home] family_title` (`config/home_settings.py`, empty by default, the family view's
`<h1>` falls back to "Our photos"), in `config.toml.j2`, docs en + fr, a test.

Left: *On this day* (a month-day query over the index, its API in the phone's list, the
thumbnails), and the *Latest additions*, *Slideshow on the TV*, *Map* entrances. The *Map*
entrance needs a decision: the places page writes `config.toml`, a phone is read-only —
a read-only map for the phone, or no map there?
