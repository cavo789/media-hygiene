# 0711 — Detect photos shown sideways (no EXIF orientation) and offer to turn them

- **Priority**: Medium
- **Batch**: slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/scan/visual.py`, `src/media_hygiene/scan/exif.py`, `src/media_hygiene/faces/`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/review/` (new page), `src/media_hygiene/actions/`, `documentation/en|fr/`

Reported by the maintainer on 2026-11-11 after a one-hour random show on the TV.

## Context

The slideshow already applies the EXIF orientation (`slideshow/screen_jpeg.py`). Photos
still shown sideways carry no orientation tag: scans, pictures passed through a messaging
app or an editor that dropped it. Only the pixels can tell.

## Proposal

1. **Which files** — only camera photos, never screenshots, game captures, drawings,
   scans of documents or collages (two of the three wrong turns measured below were not
   photos: a video-game dog, a collage):
   - the EXIF says a camera took it (`camera` of `VisualFacts`: make or model present);
   - and its make is not a games console or a screenshot tool (a short list of makes, e.g.
     `Nintendo`: `HNI_0012 (6).JPG`, A15, is likely a Nintendo 3DS capture — *not checked*:
     read its EXIF before writing the list); names of screenshots (`name_patterns`) left out;
   - photos without any camera EXIF (WhatsApp, scans) are left out of the first version;
     a later TODO may add them once measured.
2. **The guess** (at audit time, in the worker that already decodes the photo; cached in
   the index with the other visual facts, schema bump; only for photos whose tag is none,
   `0` or `1`):
   - faces found in the 4 turns (existing YuNet), the turn with the best total score;
   - proposed only when it beats the stored turn by a clear margin (A18: a girl lying down
     on an upright photo) — margin chosen from the measure, a named constant;
   - **180 deg only when two faces or more agree** (2 of the 3 errors were 180 deg; cameras
     seldom store a photo upside down without a tag).
   - Also read the tags `90` / `180` written in degrees by some software (12 photos):
     treated as the EXIF codes 6 / 3 everywhere pictures are shown upright.
3. **Seeing first** (0524): a page "Photos to straighten", tiles from the shared `pick_*`
   templates (skill `photo-picking-pages`), each tile shown as it would be after the turn;
   untick to refuse (refusals remembered, not proposed again); *Apply now* (`ApplyOffer`).
4. **The turn**: lossless — write the EXIF orientation tag (the pixels are not touched),
   journaled like the other writes, undone by `undo`; protected folders never written.
   The index, previews and thumbnails follow (new mtime: new preview key).
5. Entry points: a line of the audit's "What next" when some are found, the home page's
   card, the docs (`commands/` page or a section of an existing one, both languages).
6. The slideshow does not guess at display time (a wrong turn on the TV is worse than a
   photo shown sideways): it shows the photos once turned.

## Acceptance

- Step 48 of `mh-measure.ps1` run again with the rules: at most 1 wrong turn in 30 proposed
  (*measured* before: 3 in 33), the time per photo given.
- A screenshot, a console capture, a collage and a person lying down in the tests (synthetic
  pictures with a fake face finder): none proposed.
- Turn, then `undo`: the file is byte-identical to before; the thumbnail follows.

## Measured (maintainer's PC, `mh-measure.ps1` step 48, 2026-11-11)

- Orientation tags of 38,438 pictures (headers read in 88 s): `1` 25,147; `6` 5,522; none
  4,203; `0` 2,413; `8` 496; `3` 209; **`90` 10 and `180` 2** (degrees written by some
  software instead of the EXIF codes: not applied today, worth reading too); unreadable 436.
- Untagged (none or `1`; `0` was left out of that run): 2,237 guessed in 300 s, **0.13 s per
  photo** (4 detections, decode at 1280 px). 33 would be turned (1.5 %).
- By eye: of those 33, **30 turned right, 3 wrong** (A15 a cartoon dog turned 180 deg: an
  animal's head taken for a face; A16 a collage of photos in several directions, 180 deg;
  A18 a girl lying down on an upright photo, 270 deg); 20 photos with faces left as they
  are: **0 missed**.
- *Estimated* for the whole collection: ~29,350 untagged + 2,413 tagged `0` → about 470
  sideways photos with faces (1.5 %); 31,800 × 0.13 s = ~69 min on one core, once (the
  index keeps the answer), ~17 min on 4 workers. Photos without faces: not measured (the
  guess says nothing on them).

So: faces are reliable enough to **propose** (91 % right among those flagged), never to
apply blindly — the page that shows them before Apply stays mandatory (3 in 33 wrong).
Rules for the guess, from the three errors: propose 180 deg only when two faces or more
agree (2 of the 3 errors were 180 deg; cameras seldom store upside down untagged), and only
when the best turn beats the stored one by a clear margin (a person lying down).
Also read the tags `90`/`180` (degrees) some software wrote: 12 photos.
