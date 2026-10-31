# 0547 — Albums never slow a page: no full hashing while a page lists or opens albums

- **Priority**: Critical — the maintainer's home page froze at ~400 % CPU for minutes (2026-10-31)
- **Batch**: share
- **Depends**: —
- **Files**: `src/media_hygiene/share/album_store.py`, `src/media_hygiene/share/album_follow.py`, `src/media_hygiene/services/slideshow_pick.py`, `src/media_hygiene/services/album_reader.py`, `tests/unit/test_album_follow.py`

## Seen (maintainer, 2026-10-31)

`docker stats`: the `mh home` container at 466 % CPU, 731 MB, for minutes; every page slow.
Removing the two "Envoi …" albums (one of 240 entries, made by a send to the TV this morning)
from `albums.json` by hand fixed it. A user cannot do that: it is a bug of the application.

## Cause (measured: `py-spy dump` inside the running container)

The 6 decode workers were idle; 4 threads of the main process were all in:

```
listing (services/album_reader.py:68) → _seen → picked_slides → album_paths
  → AlbumStore.on_disk (share/album_store.py:89) → follow → _seek
  → _same_content (share/album_follow.py:165)
```

Three costs multiply:

1. **Every album re-checked once per album.** `album_paths(name)` calls `on_disk()`, which
   follows the entries of *all* albums; `listing` calls it for each album → N² checks.
2. **A missing file means full SHA-256 of many files.** `_same_content` takes every index row
   of the same size and runs `full_digest` on each one whose `full_digest` is NULL — most rows
   (the audit stores the partial digest only). One lost file = several photos read in full.
3. **Nothing is remembered.** A file still missing is searched again at each page load, each
   request, in parallel (4 requests at once seen).

Why the "Envoi" albums: their entries were not found at their path (count to check: how many of
the 240, and why — host path mapping of a send, a file since moved, or a path never on disk).

## What

The rule: **opening or using a page never costs more than reading `albums.json` and a few index
queries**, whatever the albums hold.

- `album_paths` / `picked_slides` follow only the album asked; `listing` reads the shelf once.
- On a page request, following a moved file uses only cheap facts: the recorded moves
  (`_moved`) and the `full_digest` values already in the index. Never compute a digest there.
- A file still missing is remembered as missing (in the shelf's `missing`, with the time it was
  checked) and not searched again on each request; a real search for lost files runs in the
  background (one thread, bounded, `nice`), or at the next audit, which already hashes — then
  the album is rewritten through `write_albums` and the page shows "found again" from disk.
- The album card shows "N photos not found" (already in `missing`) — never a slow page.
- Find why the send-to-TV album held entries not on disk; fix at the source (see 0548 on
  whether a send should make an album at all).

## Tests

- An album of 240 entries all missing, the index holding 500 same-size files without
  `full_digest`: `listing` returns with `full_digest` never called (monkeypatched to fail).
- 6 albums: `on_disk` follows each entry once per listing (count calls).
- A file moved by `sort` (recorded move) is still followed on the page; a file moved by the user
  is found again by the background search / next audit, not by the page.
- Gain to report: the maintainer's case, before (minutes, 400 % CPU, measured) → after (target:
  the albums list under 0.5 s, to measure with the same albums file put back).
