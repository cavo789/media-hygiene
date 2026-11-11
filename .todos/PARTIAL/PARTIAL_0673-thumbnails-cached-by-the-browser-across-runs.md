# 0673 — Thumbnails kept by the browser across runs: content-named URLs, never asked again

- **Priority**: High
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/report/preview_cache.py`, `src/media_hygiene/search/pictures.py`, `src/media_hygiene/search/hits.py`, `src/media_hygiene/places/photos.py`, `src/media_hygiene/person/pictures.py`, `src/media_hygiene/review/respond.py`, `src/media_hygiene/review/local_app.py`, `tests/unit/`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

A tile's picture is `/thumb/<index key>.jpg`, answered `Cache-Control: private, no-cache`
with an `ETag` drawn **per run of the server** (`RUN_TAG`, `review/respond.py`; read
2026-11-10). So: (1) within a run, the browser still asks the server for every tile it shows
again (a 304 each, one connection each); (2) after any restart of the server — and `mh`
restarts it around steps and page switches — every tile is **sent again**, although the
picture did not change and sits in `/cache/previews`.

The stable name already exists: `preview_key()` (`report/preview_cache.py`) hashes the
file's path, size, modification time, the edge and the preview version. *Measured*
(devcontainer, 2026-11-10): a 360 px thumbnail of a 12 MP JPEG is 6.4 KB; served from the
disk cache in 1.0–1.2 ms, each on a new connection.

## Proposal

- The hits carry `/thumb/<preview_key>.jpg` (and the same for `/preview/`): answered
  `Cache-Control: private, max-age=31536000, immutable`. A file edited gets a new key, so a
  stale picture can never be shown; the server maps key → file through the index (a small
  table or an in-memory map filled as hits are listed; an unknown key: 404, the page lists
  again).
- Faces (`/face/3.jpg`, numbered per run) keep today's rule unless they get a stable key too.
- Apply the workflow rule on caches: list every event that changes a picture — edit in
  place, replace keeping the mtime, rename, move by `sort` / `undo` / quarantine, a folder
  renamed in Explorer, a preview version bump — and keep one test per event. A rename
  changes the key (the path is in it): accepted (one more render), or key by content digest
  where the index has one — decide with the figures.
- Privacy unchanged: `private`, same doors, same pairing; the key reveals nothing (a hash).

## Acceptance

- [ ] Reopening a page already seen: 0 request for its tiles (headless Chromium, counted),
      also after a server restart
- [ ] One test per invalidation event above
- [ ] Requests and bytes for a 200-tile page, second visit, before / after, in the PR

## Where the user gains

Second visit of a 200-tile page: 200 requests → 0; after a restart of the server about
1.3 MB re-sent → 0 (estimated from 6.4 KB a tile, measured). The phone gains most (each
request is a TLS connection today).

## Status — PARTIAL (2026-11-11)

### Done

- `search/stable_pictures.py`: the hits of the search/library/browse page carry
  `/thumb/<key>.<tag>.jpg` and `/preview/<key>.<tag>.jpg`, `<tag>` = `preview_key()` of the
  index row (path, size, mtime, edge, preview version). `search/pictures.py` answers
  `private, max-age=31536000, immutable` (`review/respond.IMMUTABLE_S`) when the file on disk
  still matches the row; a file changed since the audit is shown under today's `no-cache`
  rule; a tag that is not the row's: 404. Names without a tag keep today's rule.
- No index table or memory map needed: the key is the row, the tag checks it (survives a
  restart). Phone allow-list (`lan_paths`, prefix-based) and 0682's caps unchanged: fewer
  connections only.
- One test per event (`tests/unit/test_stable_pictures.py`): edit in place, replace keeping
  the mtime, move/rename (Explorer, `sort`/`undo`/`clean --repair`, quarantine), preview
  version bump, a row reused by another file, unknown/odd names, legacy names, the header.
- Measured (devcontainer, 200 synthetic 12 MP JPEGs, `Pictures.answer`, scratchpad script):
  200 thumbnails = 4.08 MB served; old names 0/200 kept for good, new names 200/200.

### Not done

- The other tile servers keep the per-run `ETag`: person, people, places, reviews, events
  (`review/events_views.py`), the slideshow/TV, albums and the album link door (`share/`,
  which parses integer keys in `review/doors.py`), the found/tag-drop desks' sample thumbs.
  Each needs its own key → version lookup; follow-up per server.
- The headless-Chromium request count (Playwright, CI only): not written; the header is
  tested instead.
- Accepted limits (reviewer): a file replaced with the same size and mtime keeps its tag
  (as the disk cache); a file moved by the user stays shown from the browser's copy until
  the next audit rewrites its row (same photo, not stale content); a change of rendering
  without a `_VERSION` bump keeps old pictures for a year — bump `_VERSION`.
