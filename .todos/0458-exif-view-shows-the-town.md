# 0458 — Large view, key I: the town of the GPS position next to the coordinates

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/exif_facts.py`, `src/media_hygiene/geo/`, `documentation/en/`, `documentation/fr/`

## Why

The maintainer, 2026-10-29 (inbox, 0446 question 2): the EXIF panel shows bare coordinates; the
nearest town (and country) from the offline gazetteer reads better. No position leaves the machine.

## Acceptance

- A photo with GPS shows "town, country" next to the coordinates; one without GPS shows nothing more.
- A unit test with a known point of the vendored GeoNames snapshot.
