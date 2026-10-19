# 0237 — `places`: give a cluster's photos to a place already named, photo by photo (wrong GPS)

- **Priority**: Medium
- **Batch**: places
- **Depends**: 0233
- **Files**: `src/media_hygiene/config/classify_places.py`, `src/media_hygiene/config/classify_settings.py`, `src/media_hygiene/places/config_photos.py` (new), `src/media_hygiene/places/board.py`, `src/media_hygiene/places/clusters.py`, `src/media_hygiene/places/app.py`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/classify/place_match.py`, `src/media_hygiene/classify/whereabouts.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_classify_places.py`, `tests/integration/test_places_command.py`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`

## Seen

Maintainer, 2026-10-17 (`mh places`, screenshot): an unnamed cluster in a village holds photos
taken at **Geer** (the grandparents' house), a place already named. The photos *were* taken at
Geer: their GPS position is wrong (elsewhere in the village). Why: not checked — likely a phone's
position indoors (Wi-Fi or cell positioning), *estimated*.

## Decided (maintainer, 2026-10-17)

- **Not** a larger circle: it would name the whole village Geer.
- **Not** a second zone under the same name: a real photo taken at that spot of the village
  would become Geer.
- **These photos only**: the photos of the cluster are given to Geer one by one; their GPS is
  ignored for the place. A later photo with the same wrong position asks again.

## Design

- Saved in `config.toml` (the only file under `/config`), with tomlkit like the places (comments
  kept, atomic, read back and shown): `[[classify.place_photos]]`, `place = "Geer"`,
  `photos = [{ sha256 = "…", path = 'C:\Photos\2019\IMG_1234.jpg' }, …]`.
- **Matched by content, not by path** (workflow rule: anything stored by path must survive
  moves): the full SHA-256 is computed when saving (the index keeps it when the exact pass did);
  `path` (host path) is for the reader only. `classify` hashes only the files whose **size** equals
  a listed photo's (size is stored too) — no full-collection hashing. So `sort`, `undo`, the
  quarantine and a folder renamed in Explorer change nothing; a photo edited in place (new content)
  falls back to its GPS — said in the docs.
- `classify`: a listed photo takes its place before `place_at` (GPS); its trip, if any, is
  measured from that place. A place renamed on the map renames its `place_photos` entry; a
  place deleted asks whether to drop its photos too (never leaves an entry naming nothing:
  `ClassifySettings` refuses a `place` that is no `[[classify.places]]` name).
- The map: a cluster whose photos are all given to a place leaves the unnamed list (as one set
  aside, 0234); partly given, its count drops; the place's tooltip says "+ 3 photos placed by
  hand".

## To do

1. In the drawer of a cluster (0233): "Give these photos to… ▾", the places with the **nearest
   first** and its distance ("Geer — 1.4 km"); each thumbnail has a checkbox, all checked by
   default (uncheck the photo that really was taken in the village).
2. `config_photos.py`: read, add, remove, rename; `POST /api/place-photos`.
3. The place's editor lists its hand-placed photos (thumbnail, host path), each removable.
4. `classify` (`whereabouts` / `place_match`): the listed photos first, by size then SHA-256.
5. Tests: save then read back; a listed photo moved and renamed still matched; an edited one
   not; a place renamed / deleted; a size collision with another file not matched; comments of
   `config.toml` kept.
6. `config.toml.j2` comment, `i18n_update`, docs EN + FR (`commands/places.md`, sort step 6);
   `docs_screenshots` to run.
