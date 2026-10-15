# 0164 — Docs `places` map: the Genval lake series shows 3 photos, not 4

- **Priority**: Low — a docs capture only; no user data involved
- **Batch**: docs
- **Depends**: —
- **Files**: `tests/support/docs/events.py`, `tests/support/docs/scenario.py`, `src/media_hygiene/places/`, `documentation/en/images/places.webp`, `documentation/fr/images/places.webp`

## Context

TODO 0121 (commit 3041eba, `/todo:iterate` of 2026-10-14) added GPS EXIF to the synthetic
lake photos of the docs scenario (Genval) and a capture of the `places` map. In that capture the
lake series appears as an unnamed cluster of "3 photos", where the scenario writes the position
into 4 pictures (as reported by the subagent of that run; to check).

Decided in the review of 2026-10-15 (maintainer): investigate, do not leave it unexplained.

## To do

1. Find why one picture is missing from the cluster: no GPS written (a picture made after the
   EXIF step, a format without EXIF), removed earlier in the scenario (`clean` quarantined it as
   a duplicate), skipped by the index, or a clustering edge (cell boundary).
2. If the scenario is wrong: fix it so the count is the one the page text implies. If the map
   drops a picture it should count: fix the code, with a test (a series of N positioned pictures
   gives a cluster of N).
3. A change to the scenario or the map makes the capture stale: run `docs_screenshots` only with
   the maintainer's go-ahead (heavy for the PC).

## Decided (2026-10-15)

- The maintainer gives the go-ahead (`/todo:iterate` of 2026-10-15): run `docs_screenshots`
  in this run if the fix changes the scenario or the map, `nice -n 19`.
