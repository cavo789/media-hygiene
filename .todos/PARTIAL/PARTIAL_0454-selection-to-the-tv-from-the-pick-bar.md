# 0454 — The pick bar sends the selection (or the whole page) to the TV, no album needed

- **Priority**: Medium
- **Batch**: slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/pick_acting.html.j2`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/review/album_show.py`, `src/media_hygiene/services/slideshow_here.py`, `src/media_hygiene/slideshow/desk.py`, `src/media_hygiene/share/album_api.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`, `documentation/en/commands/album.md`, `documentation/fr/commands/album.md`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `documentation/en/commands/browse.md`, `documentation/fr/commands/browse.md`

## Why

The CLI already shows a folder or a search on the TV (`slideshow --folder`, `--search`), but
every launch without a console knows only albums (home page step *Show an album on the TV*,
`/slideshow/album/<name>`, 0417). To show a period filtered in `search` or a folder such as
`2026/11/Valkenburg`, the user must first make an album: a detour for nothing. The album stays
useful to keep a hand-picked selection and show it again; it is not the way to the TV.

## What (decided with the maintainer, 2026-10-28)

1. **📺 On the TV** in the shared `pick_*` bar (skill `photo-picking-pages`: every tile page gets
   it, at the same place): active as soon as one photo or video is picked; the click starts the
   show **in the home server** with those files (like `/slideshow/album/<name>` today: a JSON
   `POST` with the keys, loopback/paired `Host` rules unchanged) and opens the remote at once.
2. Nothing picked: the same button offers **everything the page shows** (the search's result,
   the folder's files).
3. **Cap**: the same `MAX_ADDED` (3000, `share/album_api.py`), one constant, not a setting; more
   files → the page says to narrow the search (same message as the album).
4. **A show already running is replaced** by the new one; the remote says so (one line), the TV
   paired stays paired (no new code).
5. The selection lives as long as the show (in memory, as today): a TV reload loses nothing; it
   is gone when `mh` stops. Nothing written but the cache's TV images and thumbnails.
6. Videos of the selection play as they do in an album.

## Docs (both languages)

`slideshow.md`: the three sources, then "from any tile page: 📺 On the TV"; `album.md`: the album
as *a selection to keep*, not the way to the TV; `search.md`/`browse.md`: the button. Captures
become stale: say `docs_screenshots` should run (never run it unasked).

## Tests

Picked files → show started with exactly them, in order; empty pick → the page's files; 3001
files refused with the message; a second send replaces the running show; a key that is not in
the index is refused (never a path from the request).

## Status — PARTIAL (2026-10-28)

### Done
- 📺 On the TV in the shared pick bar (`pick_acting.html.j2`, `pick_grid.js.j2`), shown when the page can reach a show (`tv_here`): `search` and `browse` opened from the home page.
- Picked files, or nothing picked → every file of the page (`all` when the search holds more than it shows); keys resolved by the page's picker through the albums API (`action: "tv"`), never a path from the request.
- Cap `MAX_ADDED` (3000) with the album's message (`_too_many`); a running show replaced, the TV stays paired; the remote opens in a new tab (`services/slideshow_selection.py`, `SlideshowHere._begin`, `Pick.files`).
- Docs en/fr: slideshow, album, search, browse; 5 strings translated; tests `tests/unit/test_tv_selection.py`.

### Not done
- The button on the review pages, `/person` and the phone page (`review_kinds.py`, `reviewing.py`, person).
  **Reason:** not wired in this run; the server side (`action: "tv"`) is ready for them.
- The "replaced" line is shown in the page's bar, not on the remote (deviation).
  **Reason:** simpler; move it to the remote if the maintainer prefers.
- "Nothing picked → the page's files" not tested in a browser; `docs_screenshots` to run (bar captures stale).
  **Reason:** no Chromium run here; captures are never regenerated unasked.
