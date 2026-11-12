# 0545 — Keep each photo's landmark and town in the index: searchable, shown, scanned once

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/services/slideshow_places.py, src/media_hygiene/geo/landmarks.py, src/media_hygiene/index/, src/media_hygiene/review/templates/pick_*, search, src/media_hygiene/classify/folder_towns.py, src/media_hygiene/geo/gazetteer.py

## Decided (2026-11-06, maintainer, start of /todo:iterate)

- Filled automatically and offline by every `audit`/`import`; a scan with a progress line, visible on a page, for the photos already indexed.
- Label and folder names: the user's own place, else the town. The GeoNames regions (admin1, admin2) are stored and searchable, never in folder names.

Left by the run to the existing rules, not asked: the 200 m radius stays a named constant (few settings); the building shown (item 7) stays with 0589 and 0489, out of this TODO; the measured share of landmarks stays with 0489.

## Context

The maintainer saw "Montagne de Bueren" in the slideshow's place corner for
`C:\Photos\2026\2026-10\Promenade à Liège\20261029_124120.jpg` (2026-10-31), then looked
for it on the PC and could not find it: it is in no tile, in no large view, and nothing
can search for it. The cause: the name is not stored. `services/slideshow_places.py`
works it out again at each show from the GPS position (user's place > OSM name in
`/cache/place-names.json` (0474) > GeoNames landmark within `NEAR_M` = 200 m > town).
The maintainer's remarks: "not very efficient, no cache?" and "searching for Montagne de
Bueren will never find the photo".

## Wanted

1. **Store it once**: the landmark (and its source: user / OSM / GeoNames) in the index,
   next to the GPS metadata, filled by the audit/import for new photos; the slideshow
   reads it instead of recomputing it. Follow the index's (path, size, mtime) rules; on a
   move by `sort`/`undo`, the row follows (workflow.md move rules; one test per event).
2. **Search**: the landmark is a search field ("Montagne de Bueren" finds the photo).
3. **Show it**: under the date on the tile and in the large view (skill
   `photo-picking-pages`: same place on every tile page), and in the PC slideshow's
   corner like on the TV.
4. **Scan the existing collection**, like `mh tags` but without an AI model: every GPS
   photo of the index gets its offline GeoNames landmark (instant, nothing leaves the
   machine); the online OSM naming stays behind the explicit Yes asked each time
   (`[places] reverse_lookup`). Visible on a page too (memory: visible in web or
   nonexistent), with a progress line.
5. Correcting a wrong name: see 0489 (this TODO provides the storage it writes into).
6. **The town too (and its region/country)**, stored the same way and at the same time:
   the offline `Gazetteer` already gives them (`geo/gazetteer.py`, `Town`). Searchable
   ("Colmar" finds the photo), shown with the landmark ("Montagne de Bueren · Liège"). The
   maintainer's goal (2026-10-31): sort into `2017/2017-11/Alsace` with `classify`, then
   still find each photo's building and town by search. The stored town/region must be
   what `classify` folder names read (`classify/folder_towns.py`, `town_folders.py`):
   one source, no second computation.
   Caveat to tell the maintainer: GeoNames regions are the current ones (Alsace is in
   *Grand Est* since 2016; admin2 gives *Bas-Rhin*/*Haut-Rhin*): a folder named "Alsace"
   comes from the user's own `[[classify.places]]` area (`places` page), not from GeoNames.
7. **The building the photo shows** (vs. the landmark *near* where it was taken): the GPS
   only gives the nearest named monument within `NEAR_M`; a photo of the cathedral taken
   from 400 m gets nothing, and one taken next to a castle facing the other way gets the
   castle. Option to ask: an opt-in 🤖 local vision model (Ollama, like `mh tags`)
   choosing among the GeoNames/OSM landmarks within ~1 km the one the picture shows —
   offline, a short list to pick from, never a free guess. Otherwise 0489 (typed by hand).

## Questions for the maintainer (ask at run time)

- Town/region: GeoNames admin1 (Grand Est) or admin2 (Bas-Rhin) in the folder names and
  the label, or only the user's own places?
- The building shown: the 🤖 vision pick of item 7 in this TODO, a follow-up TODO, or
  only the manual 0489?
- Automatic during every `audit`/`import`, or only on demand (a verb / a home action)?
- Keep the 200 m radius, or make it a setting (memory: few settings — a constant unless
  collections differ)?
- Measure first: share of the maintainer's GPS photos with a GeoNames landmark within
  200 m (tells how useful the scan is) — via `tests/measure/mh-measure.ps1`.

## Acceptance

- [ ] The landmark and the town are computed once and stored; the slideshow and classify no longer recompute them
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
- [ ] Search finds a photo by its landmark or its town; tiles and large view show it
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
- [ ] A scan fills it for the existing GPS photos, offline; tests for moves/renames
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
- [ ] Both languages of the docs updated; `docs_screenshots` flagged as stale
  → captures: one run of `docs_screenshots`, tracked in 0717 (2026-11-12)

## Decided (2026-11-05, maintainer, start of /todo:iterate)


- Label and folder names: town + admin2 (Colmar · Haut-Rhin); a folder "Alsace" still comes from
  the user's own `[[classify.places]]`.
- Filled automatically by `audit`/`import` for new photos, plus a visible action on a page for the
  existing collection, with a progress line.
- The building shown (item 7) is not in this TODO: see 0589 (🤖 local vision); 0489 stays the
  manual way.
- The 200 m radius stays a constant.

## Status — PARTIAL (2026-11-06)

### Done
- Index table `spots` (schema 19, a row of `PATH_TABLES`: follows `sort`/`undo`/`clean`): landmark and source (`user`/`osm`/`geonames`), town, admin1, admin2, country, searched words. Trusted only while the file records that position; refilled when the snapshot, `[tags] town_km` or the names of towns change; a `user` name is never replaced (0489 writes it).
- Snapshot: admin2 added (`districts.tsv.xz`, 7th column of `towns.tsv.xz`, `admin2Codes.txt` in `geonames_update`).
- Filled by every `audit`, by the verb `spots` (home page, inline), and first by the *tags* run of the home page, with its progress line.
- Search finds by landmark, town, regions and country, without `tags`. Tiles of `library` (search, folders, heaviest), large view and the PC slideshow's status line show it. The slideshow reads the row; it works the landmark out only for a photo without a row.

### Not done
- `classify` still computes its towns: a trip's town is the largest town around a group's centre, and `folder_town` comes from the folder's name; neither is a fact of one photo, and reading the stored town would change the folders of existing sorts.
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  **Reason:** the maintainer decides whether to change these rules; no per-photo town is computed by `classify` today, so nothing is computed twice.
- The GPS line of the large view (`search/gps_town.py`), `album_reader`, `tags/place_words` still use the gazetteer.
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  **Reason:** left out to keep the change reviewable: move them to the stored row in a follow-up.
- The other tile pages (import, quarantine, phone, reviews) show no place.
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  **Reason:** their files are mostly not in the index; only `library` reads it.
- The `{region}` placeholder of `[classify] layout` is kept although the regions are "never in folder names".
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  **Reason:** only a layout the user wrote uses it; removing it would break their configuration. Question to the maintainer.

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
