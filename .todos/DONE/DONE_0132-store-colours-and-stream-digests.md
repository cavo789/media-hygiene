# 0132 — Keep colourfulness and same-stream digests in the index

- **Priority**: High — every audit, `review --near` and `clean` re-decodes every near-duplicate candidate and runs `ffmpeg` 3 times per candidate video
- **Batch**: index
- **Depends**: —
- **Files**: `src/media_hygiene/services/near_checks.py`, `src/media_hygiene/scan/colour.py`, `src/media_hygiene/services/same_streams.py`, `src/media_hygiene/scan/media_payload.py`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/index/rows.py`, `src/media_hygiene/index/facts.py`, `src/media_hygiene/scan/models.py`, `src/media_hygiene/scan/video_models.py`, `documentation/en/start/02-keep-the-cache.md`, `documentation/fr/start/02-keep-the-cache.md`

## Context

Speed review of 2026-10-14. `services/near_checks.checked_similar` measures the colourfulness of
every picture and video that `find_similar` found alike. Its docstring says: *"nothing is stored,
so a later audit measures them again"*; the comments on `VisualFacts.colour` and
`VideoLook.colour` say *"never stored"*. Each run therefore:

- decodes every candidate image again (`image_colour`: Pillow draft + resize, run with
  `asyncio.to_thread`, so the GIL limits it);
- for every candidate video, runs `ffmpeg` 3 times (`_VIDEO_POSITIONS`), each with a 60 s
  time limit.

`services/same_streams._digests` likewise SHA-256s the whole picture and sound payload of the
re-encoded video groups whose box sizes match (`scan/media_payload.payload_digest`), on every
run.

In a collection that does not change, these values never change. They depend only on the file's
bytes, like the other facts kept under (path, size, mtime).

## What to do

1. New nullable columns in `files`: `colour REAL`, `colour_version INTEGER`, `stream_digest TEXT`,
   added by `schema.prepare` like the previous columns (schema version + 1). The version lets a
   change of the measurement re-measure.
2. `checked_similar`: read the stored colour first and measure only the files that lack one, then
   store what was measured. The same for `payload_digest` in `same_streams`.
3. Images: measure in the process pool (`runtime.executor_factory`) instead of `to_thread`.
   This matters for the first run only.
4. Update the comments "never stored" and the docstring of `near_checks.py`.
5. Docs en + fr (`start/02-keep-the-cache.md`): the cache also keeps the colours and stream
   digests of the near duplicates.

## Acceptance

- A second audit with nothing changed runs no `ffmpeg` colour frame and opens no candidate image.
  A test with a counting fake checks this.
- A file rewritten in place (new mtime) is measured again.
- An index of the previous schema still opens (`tests/fixtures/` upgrade test).
