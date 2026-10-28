# 0449 — slideshow: the storyteller's view on the phone, and story controls

- **Priority**: Medium
- **Batch**: slideshow
- **Depends**: 0448
- **Files**: `src/media_hygiene/slideshow/templates/slideshow.html.j2`, `src/media_hygiene/slideshow/templates/slideshow.js.j2`, `src/media_hygiene/slideshow/desk.py`, `src/media_hygiene/slideshow/show.py`, `src/media_hygiene/slideshow/app.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Why

Validated by the maintainer (2026-10-28): the person telling the story reads notes on the phone
while the family looks at the TV.

## What

- **The storyteller's view** on the phone's remote: the photo shown now (larger), its event
  (0448), date **and time**, place, the people recognised (`people`, if any), its description
  and words (`tags`, if any), and the next photo. Read-only (memory `phone-read-only`).
- **Story controls**: *pause while I talk* (one tap, the show waits), *back to the start of
  this event*, *next event*.
- **A small map of the event** (its photos' positions, from the index's GPS) in the
  storyteller's view, offline: the vendored Leaflet of `places/` without tiles, or a simple
  drawing of the points over the event's towns (to decide at implementation: no tile request
  unless `[places] tiles` is set, as in `places`).

## Explicit NON-goals

- Anything that changes photos, albums or the index from the phone.
