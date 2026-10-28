# 0374 — `album`: the folder follows the album, links of photos taken out removed

- **Priority**: Low
- **Batch**: share
- **Depends**: —
- **Files**: `src/media_hygiene/services/album_logical.py`, `src/media_hygiene/services/album_folder.py`, `src/media_hygiene/actions/album_plan.py`, `tests/integration/test_album.py`, `documentation/en/commands/album.md`, `documentation/fr/commands/album.md`

## Context

Review of the feedback of 2026-10-22 (0298), maintainer 2026-10-25. `album "Crete 2023" --apply`
makes the folder of hard links of a saved album; a photo taken out of the album since stays in
the folder: the folder only grows.

## What to do

1. The dry run also lists the links of the folder whose photo is no longer in the album (a link
   is known by its inode = an album entry's file).
2. `--apply` removes those links only (never a file that is not a hard link to a photo of the
   library: its only copy), journaled; `undo` puts them back.
3. Tests: a photo taken out → its link listed, then removed; a file copied into the folder by
   hand → never touched; undo. Docs en + fr.

## Acceptance

- After taking photos out of an album, `album <name> --apply` leaves the folder equal to the album.

## Decided (2026-10-27)

By the maintainer: a stale link's other name (the photo to link back from at `undo`) is
found through the index: a file of the same size with the same `(st_dev, st_ino)`. A link
whose other name lies outside the analysed folders is left in place; a file with
`st_nlink == 1` (copied by hand: its only copy) is never touched. Design proposed in the
run of 2026-10-27: split the undo machinery (`actions/reversal.py` is at the 200-line cap)
before adding the new journal kind.
