# 0085 — Place tags say their kind, so `xmp` fills City, Country and Location

- **Priority**: Low
- **Batch**: tags
- **Depends**: —
- **Files**: `src/media_hygiene/tags/producers.py`, `src/media_hygiene/tags/models.py`, `src/media_hygiene/index/tag_rows.py`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/tags/xmp_merge.py`, `src/media_hygiene/services/xmp_plan.py`, `tests/unit/test_xmp_merge.py`, `tests/unit/test_tag_producers.py`, `documentation/en/reference-tags.md`, `documentation/fr/reference-tags.md`

## Context

TODO 0074 (closed) writes the tags into `.xmp` sidecars: `dc:subject` and `dc:description`,
with our values tracked in the `mh:` namespace. Photo managers (digiKam, Lightroom, Immich)
also read the location fields `photoshop:City`, `photoshop:Country` and
`Iptc4xmpCore:Location`, and show them apart from the keywords.

`tags/producers.place_words` returns words only: the user's places (`[[classify.places]]`),
then the GeoNames town and its country within `[tags] town_km`. The `tags` table stores
`(path, size, mtime_ns, source, value, model)`, so `xmp` cannot tell a town from a country, and
all place words go into `dc:subject` only.

## Steps

- [x] Give each `place` tag its kind (`personal`, `town`, `country`): a new column of `tags`
  (schema upgrade in place, existing rows read as unknown kind until the next `tags` run), or a
  sub-source; choose the one that keeps `search`'s `place:` column working.
- [x] `xmp_merge`: fill `photoshop:City` (town), `photoshop:Country` (country) and
  `Iptc4xmpCore:Location` (the first personal place), only when the field is empty or still
  ours (tracked in `mh:` as `dc:subject` is); a value set by another application is never
  replaced.
- [x] `undo` unchanged: the whole sidecar is restored or removed as today.
- [x] Tests: a new sidecar gets the three fields; a Lightroom-like sidecar with its own City
  keeps it; rerun writes nothing.
- [x] Docs en/fr `reference-tags.md` (`xmp` section: the fields written).

## Acceptance

- exiftool reads `City`, `Country` and `Location` from a sidecar written by `xmp`, and a
  sidecar whose City came from another application keeps it.

## Status

DONE (2026-10-11, night run, second pass). Place tags carry a `kind` (`tags.models.PlaceKind`:
personal, town, country) in a new `tags.kind` column (index schema 7, added in place; rows of
an older run read as unknown until `tags` runs again; a read-only version 6 index — `search` —
reads them as unknown too). `search`'s `place:` column is unchanged (still one source).
`tags/xmp_places.py` fills `photoshop:City`, `photoshop:Country` and `Iptc4xmpCore:Location`
(tracked in `mh:city`, `mh:country`, `mh:location`), element or attribute form read, another
application's value kept, ours removed elsewhere not written again. `xmp_owner` counts the
three fields as ours. Checked with exiftool on a new and a Lightroom-like sidecar.
Report: `.claude/plans/night-2026-10-10/0085-report.md`.
