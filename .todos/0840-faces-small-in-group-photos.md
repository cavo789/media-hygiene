# 0840 — Small faces of group photos: detection by tiles

- **Priority**: High
- **Batch**: faces
- **Depends**: none
- **Files**: `src/media_hygiene/faces/detect.py`, `src/media_hygiene/faces/worker.py`, `src/media_hygiene/person/second_look.py`, `src/media_hygiene/services/people_find.py`, `tests/unit/`
- **Needs maintainer**: the path of the group photo of 2026-11-15 (terrace, ~9 people, no face found), to measure before and after

## Why (maintainer, 2026-11-15)

A sharp group photo taken at a few metres: no face found by the audit, nor by the second
look. Estimated cause (not measured): the detector sees the photo shrunk to
`DETECT_SIDE` = 640 px, where each face is 15–25 px wide; heads bent or in profile then
stay below `MIN_SCORE` = 0.9. The second look turns the picture but keeps 640 px.
A similar photo had every person named by hand: names only help once a face is detected.

## Idea

- Detect on overlapping 640 px tiles of the full-size photo too, boxes mapped back,
  duplicates merged (`OVERLAP`).
- First in the second look (one photo, the user waits for it), then in the audit for the
  photos where the whole picture found nothing (or few faces for its size).
- Measure on the maintainer's photo: faces found, seconds (estimated 6–12× the detector
  passes for a large photo); a test with a synthetic picture of small faces.
