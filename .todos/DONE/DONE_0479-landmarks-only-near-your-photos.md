# 0479 — Landmarks: load only those near the user's photos

- **Priority**: Low
- **Batch**: slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/geo/`, `src/media_hygiene/services/slideshow_story.py`

## Why

0472 loads all 432,369 GeoNames landmarks (measured: 0.62 s, 268 MB peak while loading). The
maintainer, 2026-10-29: no RAM concern, but why load continents never photographed?

## Decided (2026-10-29, the maintainer)

No setting: keep only the landmarks in the one-degree cells (`geo` grid) holding at least one
photo of the index (its GPS clusters). A new trip's cell is loaded the next time. The image keeps
the whole list (+4.2 MB). The 200 m radius stays a constant.

## Acceptance

- A photo in a loaded cell still gets its landmark (Tour Eiffel test); cells without photos load nothing.
- Measure load time and peak memory before → after on the demo index (and say the figures measured).
