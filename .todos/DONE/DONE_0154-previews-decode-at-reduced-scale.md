# 0154 — Previews: decode a JPEG at the reduced scale it is shown at (2.5–3.8× faster)

- **Priority**: Medium — every preview decodes the whole picture: report thumbnails of a first audit, every photo of `review`, `review-sort`, `search` and `people`, every photo shown to the vision model
- **Batch**: report
- **Depends**: —
- **Files**: `src/media_hygiene/report/thumbnails.py`, `src/media_hygiene/report/preview_cache.py`, `src/media_hygiene/classify/ai/describe.py`, `tests/unit/test_preview_cache.py`, `tests/integration/test_report_previews.py`

## Context

Speed and cache review of 2026-10-14 (third pass). `jpeg_preview(source, edge)` calls
`upright_picture`, whose `ImageOps.exif_transpose(image)` loads the picture at full size before
`thumbnail` shrinks it. `thumbnail` would ask libjpeg-turbo for a reduced decode (`draft`: 1/2,
1/4 or 1/8 through the scaled IDCT), but only on a picture not loaded yet: here it comes too
late. The audit's own check already drafts (`inspect_image`, `ANALYSIS_EDGE`).

Measured on 2026-10-14 in the devcontainer, one process, a 12 MP JPEG of 3.4 MB, best of 4:

| Edge | `jpeg_preview` today | drafted first | |
|---|---|---|---|
| 160 px (report thumbnails) | 81 ms | 21 ms | 3.8× |
| 400 px (`review-sort` grid) | 82 ms | 22 ms | 3.7× |
| 1600 px (`review`, `people`, `search`) | 132 ms | 52 ms | 2.5× |

The preview cache (0133) already keeps each preview once per size. This TODO makes the first
report of a large collection faster, and every photo not yet seen in the review pages appear
sooner. HEIC pictures gain nothing: HEVC has no reduced decode (360–680 ms per preview, see 0155).

## What to do

1. In the preview path, for a JPEG: `image.draft("RGB", size)` before `exif_transpose`, `size`
   being the stored size reduced so that its longer side is `edge`. Draft keeps a scale whose
   result is at least that size, and the box is square, so a rotated photo is fine. Then
   `thumbnail` to the exact edge as today. RAW previews (embedded JPEG) can go through the
   same path when the embedded preview is a JPEG.
2. The photos the vision model sees (`classify/ai/describe.py`, `jpeg_preview` at
   `[classify.ai]`'s edge) get it too. Descriptions already cached are not redone (their key
   is the photo, the model and the prompt).
3. Not here: `faces/worker.py` (detection) and `people/crops.py` (face crops). A reduced
   picture changes what the face models see; measure the recognition first (0104 §4 and §6)
   before drafting there.
4. The preview cache keeps the previews made before (still valid for display): no version
   change.

## Acceptance

- Unit test: a drafted preview has the same size and orientation as before (portrait photo
  with an EXIF rotation included), and is visually close (mean absolute difference under a few
  levels on a test picture).
- The first report of the demo tree written faster (`Report written in … s.`), figure in the
  commit message.
