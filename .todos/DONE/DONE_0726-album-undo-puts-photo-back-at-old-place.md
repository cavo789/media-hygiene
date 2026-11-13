# 0726 — Album Undo puts the photo back at its old place

- **Priority**: Low
- **Batch**: albums
- **Depends**: —
- **Files**: `src/media_hygiene/share/album_store.py`, `src/media_hygiene/share/album_edit.py`, `src/media_hygiene/share/templates/album.js.j2`, `tests/unit/test_undo_toast.py`

Follows DONE 0696 (`.todos/DONE/DONE_0696-album-photo-out-undo-toast.md`, commit 54733c43): taking a photo out of an album shows an Undo toast, but Undo adds the photo back at the end of the album, not where it was.

Decided by the maintainer in the review of 2026-11-12.

## What

- `AlbumStore.add` (`AlbumChange`) accepts a position; the toast sends the old index; out of range = append.
- Several photos taken out then undone keep their relative order.

## Acceptance

- [x] Test: remove the 2nd of 5, Undo: back 2nd; position beyond the end: appended; album changed meanwhile: no error.

## Done

- `AlbumChange.at` (and `at` in `POST /api/albums`): added files go there; None or beyond the end: appended.
- `Shelf.taken` / the answer's `taken`: where the files taken out stood; the toast's Undo sends it back.
- Tests: `tests/unit/test_album_put_back.py`, `tests/unit/test_undo_toast.py`.
