# 0238 — `places`: folders named after a town, "to place" apart from "placed", sorted by name

- **Priority**: Medium
- **Batch**: places
- **Depends**: 0235
- **Files**: `src/media_hygiene/places/folder_rows.py`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_places_folders.py`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`

## Seen

Maintainer, 2026-10-17 (`mh places`, screenshot): in "Folders named after a town (53)", the
folders already placed (📌 Metz, 📌 Quimper) are mixed with those still to do (📁 Durbuy,
Vilvoorde, Brugge). Wished:

1. Two sub-sections: the folders not dealt with yet, and the folders given a position, to tell
   at a glance what is done.
2. Alphabetical order (today `folder_rows` sorts the most photos without GPS first, then by path).

## To do

1. The fold keeps its title and total; inside, two sub-lists, each with its count:
   - **To place (N)** — 📁, open by default;
   - **Placed (N)** — 📌 (a `[[places.folders]]` entry), folded by default; the folders saved but
     not found (⚠, renamed or moved) stay here, at the top, so they are seen.
   The folders set aside as "Not a town" (0235) are in neither: in the "Set aside" fold.
2. Each sub-list sorted by the name shown (the town, else the last folder name), case and accents
   ignored (`localeCompare(…, {sensitivity: "base"})`, as 0236); two folders of the same name
   (`2014\Metz`, `2019\Metz`) by host path. The photo count stays on the line.
3. Saving a position moves the line from "To place" to "Placed" and flashes it there (the
   existing `folderFlash`, the sub-list unfolded); "Forget its position" moves it back.
4. The page sorts; `folder_rows` keeps the rank it sends (the rank names a row in
   `GET /api/folder/<rank>`): sort a copy, never renumber.
5. Tests: the split (placed, to place, placed but not found), the order with accents and case,
   a save that moves a line.
6. `i18n_update`; docs EN + FR; `docs_screenshots` to run.

## Decided (2026-10-17)

- The maintainer wants a filter box too: on top of the fold, "type a name" filters both
  sub-lists live (the name shown and the host path, case and accents ignored); the counts
  show what is filtered ("3 / 41"); Esc empties it. Add it to the tests.
