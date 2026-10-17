# 0230 — `xmp`: a GPS position for the photos without one, from their folder named after a town (opt-in)

- **Priority**: Medium
- **Batch**: tags
- **Depends**: 0229
- **Files**: `src/media_hygiene/tags/xmp_gps.py` (new), `src/media_hygiene/tags/xmp_merge.py`, `src/media_hygiene/tags/xmp_doc.py`, `src/media_hygiene/services/xmp_plan.py`, `src/media_hygiene/services/xmp_towns.py` (new), `src/media_hygiene/classify/folder_towns.py`, `src/media_hygiene/config/tags_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/console/xmp_view.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_xmp_gps.py` (new), `tests/integration/test_xmp_folder_gps.py` (new), `documentation/en/commands/xmp.md`, `documentation/fr/commands/xmp.md`

## Wish

Maintainer, 2026-10-17: folders `Douarnenez`, `Saint-Jean de Luz`… hold photos without GPS.
They want those photos on the map of a third-party tool. Chosen: a GPS position in the `.xmp`
sidecar, **opt-in** (`[tags] xmp_folder_gps = true`), never by default.

## To do

1. `[tags] xmp_folder_gps = false` (default `config.toml` commented, both languages). When true,
   `xmp` gives each photo **without a GPS position** (no `located_point` in the index, no
   position in its sidecar) the position of the town its folder is named after — the same
   folder → town guess as the `folder_town` rule (`folder_towns.py`: whole name,
   `folder_town_min_population`, `folder_town_ignore`, months never, homonyms by the countries
   of the collection and home; the folder's located photos farther than `trip_merge_max_km`
   reject it), whether or not a `folder_town` rule is in `[[classify.rules]]`: expose the town
   (with its `Point`) from `folder_towns.py` without the rule check.
2. Written as XMP-exif: `exif:GPSLatitude` / `exif:GPSLongitude` in the XMP form
   `DDD,MM.mmmmmK` (e.g. `48,5.8320N`), `exif:GPSVersionID` `2.2.0.0`; tracked in `mh:gps`
   as the place fields are (`xmp_places.py`): a position another application wrote is never
   replaced; ours removed there is not written again; ours is updated when the town changes,
   taken back when the setting goes off or the folder is no town any more.
3. The location fields too: `photoshop:City` / `photoshop:Country` from that town when the place
   tags give none (same tracking rules).
4. `xmp` (dry run) says how many photos get a position from their folder, per town (top 10),
   in `xmp_view.py`; with `--apply` the journal and `undo` work as for the words (sidecars
   created removed, others restored byte for byte).
5. Tests: the XMP coordinate format (N/S, E/W, 0°, rounding); a photo with its own GPS gets
   nothing; a sidecar with another app's position is kept; ours updated, taken back; the setting
   off writes nothing; a folder `Saint-Jean de Luz` (0229); undo restores.
6. Docs EN + FR (`commands/xmp.md`: what is written, the setting, "approximate: the town's
   centre"; which third-party tools read XMP-exif GPS — **to check**: exiftool, digiKam,
   darktable, Lightroom, Immich).

## Explicit non-goals

- Writing into the photo itself: never (sidecars only).
- A precise position per folder, chosen on the map: 0231.
