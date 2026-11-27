# 0839 — Faces in videos: a few frames of each video, analysed like photos

- **Priority**: Low
- **Batch**: faces
- **Depends**: none
- **Files**: `src/media_hygiene/services/people_files.py`, `src/media_hygiene/scan/keyframes.py`, `src/media_hygiene/faces/worker.py`, `src/media_hygiene/index/face_rows.py`, `src/media_hygiene/person/scan_route.py`, `src/media_hygiene/review/templates/pick_viewer.js.j2`, `tests/integration/people/`

## Why (maintainer, 2026-11-15)

`audit --people` analyses photos only (`people_photos` keeps `PREVIEWABLE`): a video
(`DSC_0008.AVI`, a communion) never has faces, and `/person` now says "This is a video"
(`scan_route.video_said`). The maintainer asked whether videos could be searched too: not
urgent.

## Idea

- Decode a few frames per video with the keyframe machinery of `video_prints`
  (`scan/keyframes.py`, `ffmpeg` at 10–90 % of its length), run `find_faces` on each,
  merge the same person seen on several frames (`SAME_FACE`), keep the faces with the
  frame's time.
- Store them like a photo's faces (path, size, mtime); a face's thumbnail is its frame.
- `/person`, `/people`, slideshow avoid: a video is then one more file where someone is.
- Measure first (skill `measure-before-ranking`): seconds per video, how many frames are
  worth it; whether it should be opt-in (`audit --people --videos`).

## Done (2026-11-27, first lot)

- Measured on 20 real videos (read only, 4 CPUs, 9 frames, longer side 1280): decoding
  0.1–1.6 s and detection 0.1–0.4 s per video (mean ≈ 0.9 s together); 10 of 19 readable
  videos had faces, seen on most frames: five frames (`FACE_MOMENTS`) kept.
- Opt-in `[people] videos = false` (`people`, `audit --people`): `faces/video_faces.py`
  (frames, one person once per video, the sharper kept), `index/face_frames.py` (schema 24,
  a `PATH_TABLES` table: moved, parked, forgotten with the file), `StoredFace.moment`, the
  face pictures cut from their frame (`CropJob.moment`), `/person` shows a scanned video's
  faces.

## Left

- A CLI flag (`people --videos` / `audit --people --videos`) or a page toggle: the setting
  is config.toml-only for now (maintainer to choose).
- `/person` *Find its faces now* and the second look on a video (still refused, `video_said`).
- The large view's box on a video (`upright_size` reads image headers only), the slideshow
  avoid and `/people` cards played as videos: to check on real videos.
- A test of a video's frames following a `sort` move (generic `MOVE` covers it, untested).
