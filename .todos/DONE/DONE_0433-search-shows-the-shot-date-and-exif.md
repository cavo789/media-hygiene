# 0433 — search: say which date is shown (taken, from EXIF) and show the photo's EXIF

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/hits.py`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/search/templates/browse.js.j2`, `src/media_hygiene/review/templates/pick_viewer.js.j2`, `src/media_hygiene/search/views.py`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

The maintainer, 2026-10-27: looked for a group of photos by the date Windows Explorer shows
(the *modified* date), but `mh search` finds by the date the photo was **taken** (EXIF
`DateTimeOriginal`, `media_day`). The tile shows that day without saying which date it is,
and nowhere in the tool can the user see the EXIF itself, nor in Explorer without knowing
where (Properties › Details › *Date taken*, or the *Date taken* column).

## What

- The tile's date says what it is: `📷 2023-07-14` (*taken*, with the time in its tooltip);
  when the file's modified date is another day, the tooltip says both ("taken 14/07/2023
  10:32 · file modified 02/03/2025"): the cause of the maintainer's miss, visible at once.
- No EXIF date (a scan, a screenshot): the tile says *no date taken: file date used* (or
  whatever `media_day` falls back to — check `classify/dates.py`), so a missing day is
  explained.
- The large view's facts (key I) list the photo's EXIF from the index's `MediaMetadata`
  (date and time taken, camera make and model, lens, exposure, ISO, GPS place if any,
  dimensions): read-only, facts only, never judgments.
- Docs en+fr (`commands/search.md`): which date search uses, and where Explorer shows it.

## Explicit NON-goals

- Editing EXIF (never: photos are only read).
- A search by modified date.

## Status — DONE (2026-10-28)

- Tile: `📷 <day taken>`; tooltip "taken <date time> (EXIF…) · file modified <day> (the date
  Explorer shows)" when the days differ; *no date taken* with its reason otherwise (`media_date`
  is EXIF `taken_at`, else the video's recording date: no file-date fallback).
- Large view, key I: the EXIF lines (`search/exif_facts.py`) for every page whose files carry
  `exif` (shared `pick_viewer.js.j2`). GPS shown as coordinates, not a place name.
- Docs en+fr (`commands/search.md`, *Which date*, *The photo's EXIF*). `docs_screenshots` should run.
