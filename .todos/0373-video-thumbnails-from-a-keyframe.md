# 0373 — Videos get a thumbnail: a frame decoded once, kept in the cache

- **Priority**: Low
- **Batch**: videos
- **Depends**: —
- **Files**: `src/media_hygiene/scan/keyframes.py`, `src/media_hygiene/scan/video_still.py`, `src/media_hygiene/report/thumbnails.py`, `src/media_hygiene/share/album_view.py`, `src/media_hygiene/slideshow/pictures.py`, `tests/integration/test_album_phone.py`

## Context

Review of the feedback of 2026-10-22 (0297), maintainer 2026-10-25. A video of an album shows no
picture (as in the slideshow's grid on the phone). `keyframes` already decodes frames at 10–90 %
of a video's length for its fingerprint; `video_still.py` exists (check what it already gives
before adding anything).

## What to do

1. One frame (≈ 10 % of the length) as the video's thumbnail, made once and kept in `/cache` like
   the photos' previews (keyed by path, size, mtime); `ffmpeg` with the time limit of `tool_run`.
2. Used by the album page, the slideshow's phone grid, and search/browse where a video shows an
   icon today.
3. Tests: a video gets a JPEG thumbnail; a second request reads the cache; a broken video keeps
   the icon. Measure the cost per video (*measured*, synthetic clip) before closing.

## Acceptance

- Album, slideshow remote and search show a picture for every readable video.
