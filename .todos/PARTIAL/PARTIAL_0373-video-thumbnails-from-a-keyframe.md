# 0373 — Videos get a thumbnail: a frame decoded once, kept in the cache

- **Priority**: Medium
- **Batch**: videos
- **Depends**: —
- **Files**: `src/media_hygiene/scan/keyframes.py`, `src/media_hygiene/scan/video_still.py`, `src/media_hygiene/report/thumbnails.py`, `src/media_hygiene/share/album_view.py`, `src/media_hygiene/slideshow/pictures.py`, `tests/integration/test_album_phone.py`

## Context

Review of the feedback of 2026-10-22 (0297), maintainer 2026-10-25. A video of an album shows no
picture (as in the slideshow's grid on the phone). `keyframes` already decodes frames at 10–90 %
of a video's length for its fingerprint; `video_still.py` exists (check what it already gives
before adding anything).

Maintainer 2026-10-27: `mh search` with `.mov` shows a grid of "No preview" tiles; they open
Windows Explorer to see what a video is. Raised to Medium. The large view (`pick_viewer`)
already plays a video in `<video>`; check that an iPhone `.MOV` (h264, and HEVC) plays there in
Edge/Chrome, and say on the tile that a double-click plays it.
Measured by the maintainer the same day: in `mh search`, a double-click on `IMG_1775.MOV` opens
the large view with a broken `<img>` (alt text only), never the `<video>`: search does not tell
the viewer the file is a video. Fix it (and browse, same templates); a test per page.

## What to do

1. One frame (≈ 10 % of the length) as the video's thumbnail, made once and kept in `/cache` like
   the photos' previews (keyed by path, size, mtime); `ffmpeg` with the time limit of `tool_run`.
2. Used by the album page, the slideshow's phone grid, and search/browse where a video shows an
   icon today.
3. Tests: a video gets a JPEG thumbnail; a second request reads the cache; a broken video keeps
   the icon. Measure the cost per video (*measured*, synthetic clip) before closing.

## Acceptance

- Album, slideshow remote and search show a picture for every readable video.

## Status — PARTIAL (2026-10-27)

### Done
- `report/video_preview.py`: one frame at 10 % of the length (`ffprobe` then `ffmpeg`, each with
  its time limit, through `scan.video_still`), as an upright JPEG; `jpeg_preview` sends videos
  there, so `preview_cache` keeps it in `/cache` keyed by path, size, mtime like a photo's.
  Measured in the devcontainer, synthetic 30 s 1080p h264 `.mov`: 0.13 s per thumbnail (360 px),
  0.12 s for the large one (1600 px); 11 KB and 60 KB.
- Search: a video hit now carries `video` (`/video/<key>.<ext>`): the large view plays it in
  `<video>` instead of a broken `<img>` (the maintainer's bug of 2026-10-27). Its grid tile shows
  the frame.
- Browse: tiles show the frame (`thumb`) instead of a `<video>` element per tile (one decode,
  cached; HEVC tiles were blank in browsers without HEVC).
- Tests: `tests/integration/test_video_preview.py` (JPEG of the right size, cache read back,
  broken video → None), `tests/unit/test_search_video_hit.py`.

### Not done
- The album page (`share/album_view.py`) and the slideshow's phone grid (`slideshow/pictures.py`)
  still show no picture for a video.
  **Reason:** kept to the search/browse bug the maintainer hit; both pages build their own
  thumbnail addresses (`film`, `thumb` empty for videos, `test_album_view.py:80`): route their
  video thumbnails through `PreviewPool.renderer` now that it accepts videos.
- An HEVC `.MOV` in the large view: Edge plays it only with the HEVC extension installed; not
  checked on the maintainer's PC. A frame fallback (show `preview` when `<video>` errors) would
  cover it.
  **Reason:** needs a measurement on Windows + Edge with a real iPhone HEVC file.
