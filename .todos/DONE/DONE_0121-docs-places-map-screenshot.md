# 0121 — Docs: a screenshot of the `places` map, with a synthetic place

- **Priority**: Low
- **Batch**: docs
- **Depends**: —
- **Files**: `tests/support/docs/shots.py`, `tests/support/docs/served.py`, `tests/support/docs/scenario.py`, `documentation/en/sort/09-places-from-gps.md`, `documentation/fr/sort/09-places-from-gps.md`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`, `documentation/en/images/`, `documentation/fr/images/`

## Context

PARTIAL 0030 asked whether the docs should show the `places` map. Decided in review 0056
(2026-10-12): yes. The page loads real OpenStreetMap tiles in the browser while the docs are
generated; the photos and the place stay synthetic. The maintainer checked the page by hand the
same day (an OSM search drew its area).

## What to do

- In the docs scenario, synthetic pictures with GPS positions in a small cluster (a public place,
  e.g. a park in Brussels — no private address), then `places` served as `review` already is for
  its own capture (`served.py`), and a capture of the map with one named place and its circle.
- Wait for the tiles to load before the capture (network idle, with a time limit: if the tiles
  fail, the capture fails loudly rather than shipping a grey map).
- One image per language (the page follows `--locale`), referenced from
  `sort/09-places-from-gps.md` and `commands/places.md`, en + fr.
- The OSM attribution stays visible on the image (tile usage policy).

## Explicit NON-goals

- The Nominatim search in the capture (one network call per docs run is enough: the tiles).
- Workbook screenshots (decided: none).

## Acceptance

- `docs_screenshots` and `docs_screenshots fr` produce the image; `test_documentation.py` sees it
  used in both languages.

## Decided (2026-10-14)

- Go-ahead to run `docs_screenshots` in the `/todo:iterate` run of 2026-10-14, last, after the
  other TODOs (the maintainer, at the start of the run). The same run refreshes every capture
  made stale by the run's earlier lots.
