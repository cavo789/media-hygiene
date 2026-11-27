# 0811 — Undo toast for photos given to a place and for an album deleted

- **Priority**: Low
- **Batch**: page-shell
- **Depends**: —
- **Files**: `src/media_hygiene/places/templates/places_map.js.j2`, `src/media_hygiene/places/hand_desk.py`, `src/media_hygiene/places/config_photos.py`, `src/media_hygiene/share/templates/album.js.j2`, `tests/unit/test_undo_toast.py`

Left by `.todos/PARTIAL/PARTIAL_0744-*.md` (from 0521): the two confirmations on reversible
choices still asked through `window.mhAsk`.

## What

- Giving photos to a place (`places_map.js.j2` give): no question; the toast's Undo takes back
  exactly the photos just given (`take_back` per photo id, or a `take` action on the photos
  route returning the ids written), read back from `config.toml`.
- Deleting albums (`album.js.j2`): check whether `albums.json`'s `.history` copy (0691) makes it
  reversible; if so, no question and Undo restores the previous `albums.json`; else keep asking.

## Done when

`_ASKED` in `tests/unit/test_undo_toast.py` loses these two entries, each Undo proven by
reading the file back.
