# 0473 — Slideshow banner: do not repeat the place when it is the event's name

- **Priority**: Medium
- **Batch**: slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/slideshow/chapters.py`, `src/media_hygiene/services/slideshow_story.py`, `src/media_hygiene/slideshow/templates/slideshow.js.j2`

## Why

The maintainer, 2026-10-29 (seen on the TV): an event named *Valkenburg* whose place (from
`mh places`) is also *Valkenburg* shows the name twice in the banner.

## What

Drop the place from the banner (and the title card, the phone's details) when the event's name
already contains it: compare case-, accent- and space-insensitively (`Promenade à Valkenburg`
contains `Valkenburg` → place dropped; `Durbuy` vs place `Ardennes` → both kept). One rule in
`chapters.py`, used everywhere the event is told.

## Acceptance

- Unit tests: equal names, name containing the place, different names, accents/case (`Liège` / `liege`).
