# 0313 — Freeing a phone: many thumbnails stay a 📷 tile

- **Priority**: High
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/review/phone_tiles.py`, `src/media_hygiene/review/phone_session.py`, `src/media_hygiene/review/files.py`, `src/media_hygiene/review/local_app.py`, `src/media_hygiene/review/templates/phone_review.js.j2`, `tests/integration/test_phone_review.py`
- **Needs maintainer**: if not reproduced here, the console lines of a run of `mh phone --free` and the browser's network tab (status of a failing `/preview/….jpg`)

## Why

The maintainer, 2026-10-23, screenshot of the page of `mh phone --free` (Samsung A72, folder
*Vacances*, JPEGs of 3.9–6.6 MB, all held by the import under
`C:\Photos\Phone\A72 de Christophe\Vacances\`): the first 4 tiles show their photo, the
following ones (same folder, same kind of file) show the generic 📷. The 📷 is what
`phone_review.js.j2` puts in place of an `<img>` whose load **failed** (`error` event): the
tile did have a preview URL, so `TileSource.preview` found a path; the request for it failed.

## Hypotheses (none checked yet)

- The renderer returned None → 404 (`jpeg_response`): the file not found in the container
  (the import's folder mounted read-only under another path than the tile's `held`?), or a
  decode error. Unlikely for files the first tiles prove readable — to check anyway.
- Many lazy `<img>` at once: the worker pool, a time limit, or the HTTP server refusing or
  closing connections under the burst (`http.py`, 30 s timeout on reading a request). The
  "first ones work, then none" pattern points here.
- A worker of the pool dying (BrokenProcessPool) after a few renders: every later preview fails.

## What

1. Reproduce: a page with ~200 synthetic JPEGs of 4000×3000 in the import's folder
   (`tests/support/docs/` makes such pictures), opened in a browser; log each preview's status
   on the server side.
2. Fix the cause. Whatever it is, the page retries a failed preview once after a short delay
   before showing 📷, and a 📷 tile says why on hover ("the PC's copy could not be read").
3. Say in the commit what was measured (how many previews, how long, which status).

## Tests

The cause's own test (a burst of N preview requests all answered 200; or the path mapping of
the import's folder). Keep one test that a tile without a PC copy still shows 📷.
