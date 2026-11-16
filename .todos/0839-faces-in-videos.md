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
