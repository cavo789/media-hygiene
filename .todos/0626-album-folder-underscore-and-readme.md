# 0626 — Albums folder by default `_Albums`, with a read-me file at its root

- **Priority**: Medium
- **Batch**: albums
- **Depends**: 0625
- **Files**: `src/media_hygiene/services/album_folder.py`, `src/media_hygiene/search/album_root_desk.py`, `src/media_hygiene/services/album_relocate.py`, `src/media_hygiene/actions/album.py`, `src/media_hygiene/actions/album_vacate.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/review/templates/`, `documentation/en/commands/album.md`, `documentation/fr/commands/album.md`, `documentation/en/sort/12-albums.md`, `documentation/fr/sort/12-albums.md`

## Decided (maintainer, 2026-11-06)

`C:\Photos\Albums` lands anywhere among the year folders and unsorted ones, and its name does
not say the tool manages it. Default becomes `_Albums`: rejected `.Albums` (hidden on Linux
and macOS, odd on Windows). To check on Windows: `_Albums` sorts before the years in Explorer
(expected from its usual behaviour, not tested).

## Wanted

1. The default folder is `_Albums` in the `[classify] target` (both places use `_("Albums")`
   today). A `[album] root` already set stays as it is.
2. `album --apply` writes a read-me at the root of the albums folder, never in an album (it
   must not land in a selection sent to a print service):
   `LISEZ-MOI - géré par Media Hygiene.txt` / `READ-ME - managed by Media Hygiene.txt`.
3. Name and content follow mh's language when it is written; the text comes from a template.
   It says: made by Media Hygiene; no extra space; a retouch changes the original too; deleting
   a photo here leaves the original; a file you put here yourself is never touched.

## Watch out

- Changing language must not leave a second read-me: recognise both names, keep one.
- A read-me is ignored by scans, and does not stop the old folder being emptied: the move
  (0582, `album_vacate`) carries it or removes it, while still keeping and reporting a user's
  file. `undo` of the run that wrote it removes it, unless other albums remain.
- Folders already made under the old default `Albums`: check that *Move the N album folders*
  also triggers when the default changes, not only the setting. Test it (a stored path moving).
- The audit ignores the albums' folders by `.media-hygiene-album`: `_Albums` itself has no
  marker, so check the read-me at its root is not listed as a stray file by any scan.
