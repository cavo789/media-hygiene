# 0708 — Detect photos shown sideways (no EXIF orientation) and offer to turn them

- **Priority**: Medium
- **Batch**: slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/scan/visual.py`, `src/media_hygiene/people/`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/slideshow/screen_jpeg.py`
- **Needs maintainer**: a reliability measurement on the real collection (`tests/measure/mh-measure.ps1`)

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
