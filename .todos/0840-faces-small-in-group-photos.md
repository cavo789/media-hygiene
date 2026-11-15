# 0840 — Small faces of group photos: detection by tiles

- **Priority**: Low
- **Batch**: faces
- **Depends**: none
- **Files**: `src/media_hygiene/faces/detect.py`, `src/media_hygiene/faces/worker.py`, `src/media_hygiene/person/second_look.py`, `src/media_hygiene/services/people_find.py`, `tests/unit/`

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

## Measured (2026-11-15, `media-hygiene:latest`, real photo read-only)

`C:\Photos\2013\2013-04\Communion Chloé\DSC_0012.JPG`, 3216×2136, 9 people, faces
72–135 px wide (≈ 15–27 px once shrunk to 640). YuNet + SFace (`OnnxRecipe`):

| Detection | Score ≥ 0.9 (audit) | Score ≥ 0.6 (second look) | Time |
|---|---|---|---|
| Whole photo (today) | **0** (scores 0.70–0.90) | 9 | 0.03 s / 0.21 s |
| Tiles 2×2 (25 % overlap) | 4 | 9 (scores 0.83–0.92) | 0.21 s / 0.41 s |
| Tiles 3×3 | 6 | 9 | 0.31 s / 0.45 s |

So the faces are seen, just under `MIN_SCORE`: tiles raise their scores (bigger faces for
the detector). The second look (0.6) should have found the 9 on the whole photo: check
why the page said nothing (was it run?). Still to measure: false faces at 0.6 or with
tiles on ordinary photos (a sample of the collection), before changing the audit.

## Done by 0841 (2026-11-15), what is left here

`MIN_SCORE` went from 0.9 to 0.6 and the photos scanned before are topped up
(`index/face_tops.py`). Measured on "Communion Manon" (215 photos, real, read-only):
whole photo at 0.6 finds 497 faces, 2×2 tiles at 0.75 490 for 7× the detector time.
Tiles are only worth it if a later measurement shows faces still missed on large group
photos at 0.6 (e.g. under 20 px once shrunk to 640). The second look (`LOOSE_SCORE` =
0.6 = `MIN_SCORE` now) only adds the turned angles: lower it, or store its faces
(boxes mapped back to the upright photo), if photos with tilted heads still miss faces.
