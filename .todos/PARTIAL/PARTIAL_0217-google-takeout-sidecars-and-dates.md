# 0217 — Google Photos Takeout: its `.json` files travel with their photo, and give a date and a place to the files without one

- **Priority**: Medium
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/scan/takeout.py` (new), `src/media_hygiene/scan/sidecars.py`, `src/media_hygiene/constants.py`, `src/media_hygiene/index/takeout_rows.py` (new), `src/media_hygiene/index/schema_tables.py`, `src/media_hygiene/classify/models.py`, `src/media_hygiene/classify/dating.py`, `src/media_hygiene/services/classify_inputs.py`, `src/media_hygiene/tags/dates.py`, `src/media_hygiene/tags/producers.py`, `src/media_hygiene/plan/near.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_takeout_names.py` (new), `tests/integration/test_takeout_tree.py` (new), `documentation/en/reference-sidecars.md`, `documentation/fr/reference-sidecars.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`

## Context

Chosen by the maintainer on 2026-10-17 (proposal F6: "media-hygiene is open source: plan for it,
but I cannot test it"). Google Photos backs up
Android phones to Google's cloud; Google Takeout (takeout.google.com) downloads a copy of
everything as ZIP files. People leaving Google Photos, or short of space, then hold a Takeout tree
next to their own folders — and many duplicates between the two.

What a Takeout holds, from tools that handle it (checked on 2026-10-17; no real Takeout here, so
every point is "to check" on a real one by a contributor):

- One `.json` file per photo or video, holding the date taken, the place, the description and the
  original file name (`title`). Older Takeouts name it `IMG_1234.jpg.json`; newer ones
  `IMG_1234.jpg.supplemental-metadata.json` (ExifTool forum, 2024–2025).
- Names are truncated (about 47 characters for the name part, 51 for the whole JSON name: the
  sources differ), so the suffix is cut too: `.supplemental-meta.json`, `.supplemental-me.json`,
  and the photo's own name may be cut.
- A number for duplicate names goes elsewhere in the JSON name: `IMG_1234(1).jpg` ↔
  `IMG_1234.jpg(1).json` (TakeoutExtractor) or `IMG_1234.jpg.supplemental-metada(1).json` (ExifTool
  forum).
- An edited version keeps the original's name with a suffix, usually `-edited` (possibly
  truncated, and perhaps translated with the account's language: to check); it can exist without
  its original.
- `&` and `?` of a title become `_` in file names.
- Year folders (`Photos from 2019`) and album folders that repeat the same photos (GPTH's README:
  album folders mostly duplicate the year folders).
- The JSON fields used by those tools: `title`, `photoTakenTime.timestamp` (Unix seconds),
  `geoData.latitude` / `longitude` (0.0 when unknown), `description` (field names to check).

Google Takeout Helper (GPTH Neo) writes these dates into the photos' EXIF; this tool never writes
into a photo.

## What to do

- **Sidecars**: a `.json` whose name matches a media file of its folder by those rules is that
  file's sidecar: it travels with it (`sort`), is set aside with it (`clean`), and becomes an
  orphan sidecar when its file is gone. Any other `.json` is left alone (not a sidecar). The
  matching lives in a new `scan/takeout.py`, with the rules above (prefix match on truncated
  names, the moved `(n)`, the edited suffix).
- **Facts**: read each matched JSON once per version (path, size, mtime), its date, place and
  description kept in a new index table of `PATH_TABLES` (it follows moves like the other rows).
- **Dates**: a new date source `takeout` in `classify`'s chain, after the file's own EXIF or video
  date and before the name (`classify/dating.py`; `DateSource` lives in `classify/models.py`,
  194/200: move a model out first if needed); `tags` gives its date words; the place gives its
  `place` words and counts for the `place`/`trip` rules like a GPS position.
- **Descriptions**: the `description` becomes `caption` words (`TagSource.CAPTION`) when the file
  has none.
- **Year folders**: `Photos from \d{4}` joins the generic folder names (`GENERIC_FOLDERS`), so that
  between identical copies the album's folder is kept (0012). `constants.py` is full (200/200):
  move `GENERIC_FOLDERS` (or another block) to its own module first; the Takeout patterns live in
  `scan/takeout.py`.
- **Edited versions**: an `-edited` file and its original are never near duplicates of each other
  (an edit is a choice, as a black and white edit already is).
- Docs both languages: a section in the sidecar reference ("Google Photos Takeout"), one line in
  step 3 (a Takeout is one more folder to add); say what was not checked on a real Takeout.

## Explicit non-goals

- Unzipping: the user extracts the ZIP files.
- Writing the dates or places into the photos (never) or into `.xmp` sidecars (a later TODO if
  wanted).
- Partner sharing, archive and trash folders of a Takeout: left as ordinary folders.

## Acceptance

- Unit (`test_takeout_names.py`): every naming case above (old and new suffix, truncated suffixes,
  a truncated photo name, `(1)` moved, `-edited` with and without its original, `&` → `_`), and a
  `.json` that matches nothing stays a plain file.
- Integration (`test_takeout_tree.py`): a synthetic Takeout tree (year folder, album folder, JSON
  files) next to a "PC" folder: the audit pairs the sidecars, the duplicates keep the album copy,
  `clean` sets a copy aside with its JSON, `classify` dates an undated video from its JSON, `tags`
  gives its words.
- Docs both languages.

## Gain (estimated)

A Takeout merged with the PC's folders in one audit, undoable: its JSON files no longer left
behind as clutter, and the photos without a date inside (videos, screenshots, received pictures)
dated and placed by Google's record instead of going to "to check".

## Status — PARTIAL (2026-10-17)

### Done
- `scan/takeout.py` (+ `scan/takeout_folder.py`, the folder's names indexed once): a `.json`
  describing a media file of its folder is its sidecar (old and new suffix, truncated suffix and
  name, moved `(n)`, `-edited` with or without its original, `&`/`?` → `_`); any other `.json`
  stays a plain file. It travels with `sort` (`actions/sort_names.py`, `sort_folders.py`), is set
  aside by `clean` as an orphan, comes back with `undo`.
- `index/takeout_rows.py`: table `takeout` (schema 13, in `PATH_TABLES`), keyed by the photo's
  path, read once per `.json` version during the walk (`services/listing.py`, needs `/cache`).
- `DateSource.TAKEOUT` (after EXIF/video, before the name) in `classify` and `tags` date words;
  the position fills a missing GPS (`services/classify_inputs.with_takeout`), so `place`/`trip`
  and the place words use it.
- `Photos from \d{4}` is a generic folder (`name_patterns.py`, moved out of `constants.py`).
- An `-edited` file and its original are never near duplicates (`plan/near.py`).
- Tests `tests/unit/test_takeout_names.py`, `tests/unit/test_takeout_facts.py`,
  `tests/integration/test_takeout_tree.py`; docs `reference-sidecars.md` (section "Google Photos
  Takeout") and step 3, both languages.

### Not done
- The `description` as `caption` words.
  **Reason:** `TagSource.CAPTION` is a model source rebuilt from the cached vision descriptions
  (per model); a cheap caption there would be dropped or duplicated by the next `describe`.
  Needs a decision: a new tag source (`takeout`) or a caption with an empty model.
- Checks on a real Takeout (names, truncation length, translated `-edited` suffixes, field
  names). **Reason:** none at hand; documented as unchecked.

## Inbox (2026-10-19)

- The `description` as words → refiled as 0240 (own source `takeout`, maintainer's choice).
- Checks on a real Takeout: still waiting for one (material).
