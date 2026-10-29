# 0472 — Slideshow: the place of each photo on the TV (town, monument when known)

- **Priority**: Medium
- **Batch**: slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/services/slideshow_story.py`, `src/media_hygiene/slideshow/slides.py`, `src/media_hygiene/slideshow/templates/slideshow.html.j2`, `src/media_hygiene/slideshow/templates/slideshow.js.j2`, `src/media_hygiene/geo/`
- **Needs maintainer**: monuments: whether the image may grow for an offline landmark list (size to measure)

## Why

The maintainer, 2026-10-29: when a photo has GPS coordinates, show on the TV where it was taken:
the town, better the monument when known.

## Today

The TV tells the place of an **event** (0448, `services/slideshow_story.Places`): the user's
place (`[[classify.places]]`), else the nearest town of the vendored GeoNames snapshot
(`geo/data/towns.tsv.xz`). Nothing per photo.

## What

1. Per photo, a discreet line on the TV: the user's place if the photo is in one, else the town
   (same `Places` / `Gazetteer`, from the index's GPS: no disk read). Not shown when it equals
   the event's place already in the banner (see the TODO on repetition).
2. Monuments: **offline only** — no position ever leaves the machine, so no Nominatim reverse
   lookup. Option: add GeoNames landmark features (class S/L: MNMT, CSTL, CH, MUS…, to check) to
   the snapshot via `geonames_update`, matched within a short radius (~200 m, to measure).
   Measure the size added to the image and the share of the maintainer's photos it names before
   deciding. Fallback: the user names a monument as a small place in `mh places` (works today).
3. A phone/TV toggle like the event telling (`Telling`), off without GPS.

## Acceptance

- A photo in a user's place shows it; one elsewhere shows its town; one without GPS shows nothing; the screen does not jump.
