# 0417 — The reviews, people, places and the slideshow served by the home server

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/review/`, `src/media_hygiene/services/review_serving.py`, `src/media_hygiene/services/reviewing.py`, `src/media_hygiene/services/people_page.py`, `src/media_hygiene/people/app.py`, `src/media_hygiene/places/`, `src/media_hygiene/slideshow/app.py`, `src/media_hygiene/review/apply_api.py`, `src/media_hygiene/services/home_audit.py`, `documentation/en/commands/`, `documentation/fr/commands/`

## Why

Leftovers of 0357 and 0358, decided by the maintainer (inbox, 2026-10-27). `search` and `browse`
already open in < 1 s from the home page; the other pages still start a server of their own.

## What

1. Bursts, pairs, junk, gone, people, places, slideshow on the home server (0357 items 1, 3–5): the
   same pattern per page; their views build `/preview/…` from the root: make them relative like
   `near_views`. (`review-sort` goes into the search instead: see the *🗂 Events* TODO.)
2. *Apply now* shows the step running, then the page's new state (0357 item 2).
3. Memory: free idle pages; measure on a real collection (0357 item 6, a step of
   `tests/measure/mh-measure.ps1`).
4. From 0358: the home page's own audit (`page_audit`) re-reads its settings when `config.toml`
   changes; *a file that no longer loads* said on the page, not only in `docker logs`.

## Acceptance

< 1 s from the home page to each page (measure step 35 with `review --near` added).

## Status — PARTIAL (2026-10-28)

### Done: the slideshow (asked first by the maintainer, for 0444)
- `services/slideshow_here.py`: `/slideshow/…` in the home server (`HomeWithPages`), the TV
  on the home server's plain door (`EndingDoor.plain`: `/screen`, its code, show, pictures;
  `/` of that door stays the phones' certificate steps). `GET /slideshow/album/<name>` starts
  an album (one show at a time, the next replaces it) and leads to the remote. The `Screens`
  and `Changes` are the home server's: a TV paired once stays paired while it runs; a new
  show's version follows the last one's so a waiting TV moves on by itself. No show yet: the
  TV gets `tv_wait.html.j2` (meta refresh, 5 s).
- The step *Show an album on the TV*, from the PC's form or a paired phone (0444), answers
  `{"page": "/slideshow/album/<name>"}` when `mh` keeps the server up (`review/album_show.py`).
- The slideshow's addresses are relative (`services/slideshow_build.py`, `relative()` in
  `slideshow/pictures.py`); `/api/lan`'s `tv` and the console now give
  `http://<addr>:8089/screen` (works for `slideshow --lan` alone too, whose `/` still leads
  there). The remote in the home server says it is alive (`presence_kept`): the home page's
  tab may leave for it.
- A phone paired by code on `slideshow --lan` alone is paired for good (`for_good` in
  `review/lan_phones_api.py`, shared with the home page).
- Phones: `lan_paths` lets through `GET /slideshow/…` (never `/slideshow/api/lan`, the code)
  and `POST /slideshow/api/show|screens` (the show in memory, no file): deliberate, asserted
  in `tests/unit/test_slideshow_here.py` against `write_routes.CHANGES`.
- The towns (`Gazetteer`) are read once per process for the slideshow's chapters
  (`slideshow_story._towns`): measured on the demo tree (24 files, 11 shown), the first album
  1.2 s (under tracemalloc; 36 MB kept, 93 MB peak), each next album start + remote + slides
  53–58 ms; before the cache every start took 1.2 s.
- Measure on the real collection: item 12 of 0445.

### Left
1. Bursts, pairs, junk, gone, people, places on the home server (item 1 above): the same
   pattern as `near_here.py` per page, their views made relative like `near_views`.
   `review-sort` goes into the search (separate TODO).
2. *Apply now* shows the step running, then the page's new state (item 2).
3. Memory: free idle pages (an idle show could be dropped after N minutes without a remote
   or TV asking); `mh-measure.ps1` step with `review --near` added (item 3, acceptance).
4. `page_audit` re-reads its settings when `config.toml` changes; *a file that no longer
   loads* said on the page (item 4).
5. Not supported: the TV in the home server under plain HTTP `--lan` (no `/lan` certificates):
   the TV needs the plain door, which exists under HTTPS only; `mh --lan` always mounts `/lan`.
