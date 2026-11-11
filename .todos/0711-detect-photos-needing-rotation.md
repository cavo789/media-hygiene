# 0711 — Detect photos shown sideways (no EXIF orientation) and offer to turn them

- **Priority**: Medium
- **Batch**: slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/scan/visual.py`, `src/media_hygiene/people/`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/slideshow/screen_jpeg.py`

Reported by the maintainer on 2026-11-11 after a one-hour random show on the TV.

## Context

The slideshow already applies the EXIF orientation (`slideshow/screen_jpeg.py`). Photos
still shown sideways carry no orientation tag: scans, pictures passed through a messaging
app or an editor that dropped it. Only the pixels can tell.

## Proposal

- At audit time (cached in the index, keyed like the other visual facts), guess the upright
  rotation (0/90/180/270) of a photo without an orientation tag:
  1. faces: run the existing face detector on the 4 rotations; the one with confident,
     upright faces wins (reliable for people, silent on landscapes);
  2. optionally, flagged 🤖, a local Ollama vision model for the rest (slow: estimate first).
- Never rewrite a file blindly (seeing first, 0524): a page showing the photos the tool would
  turn, as tiles (skill `photo-picking-pages`), with Apply now; the turn is lossless when
  possible (set the EXIF orientation tag rather than re-encode), and undoable.
- Meanwhile the slideshow may apply a confident guess at display time only (no write).

## To measure before implementing

- Share of photos without orientation tag in the maintainer's collection, and how many of
  them are actually sideways (sample).
- Precision of the face-based guess on that sample; time per photo (4 detections).

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
