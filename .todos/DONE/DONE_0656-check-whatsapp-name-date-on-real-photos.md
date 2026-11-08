# 0656 — Check on real photos what the date in `IMG-YYYYMMDD-WA` names

- **Priority**: Low
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/classify/received.py`

## Problem

Follows 0402 (feedback of the sort convention run, 2026-10-25). Received pictures are joined to
the event nearest the **day of their name**, assuming `IMG-YYYYMMDD-WA` holds the day they were
received. Not checked on real files. Decided in the review of 2026-11-08: check it read-only on
the maintainer's collection.

## Fix

Read-only (the `C:\Photos` mount, `:ro`; nothing written there): list the `*-WA*` files that also
carry an EXIF date, compare that date with the one in the name (same day, days before, after),
and give the distribution (*measured*). If the name's date is often later than the taken day,
adjust `classify/received.py` (wider window, or before only) and its tests.

## Acceptance

- [x] The distribution measured and written here (count, median gap, how many are the same day): 0 files, see Result
- [x] `received.py` changed only if the measure says so: not changed (nothing to measure)

## Result

*Measured* 2026-11-08, read-only: a Python script run in `media-hygiene:latest` (`--network none`,
`C:\Photos` bind-mounted `readonly`, `#recycle` skipped), walking every file and matching
`-WA\d` in the name, then comparing the name's day with EXIF `DateTimeOriginal`.

- 39 793 files walked (37 225 `.jpg`, 756 `.mp4`, 471 `.png`, 436 `.heic`, 293 `.jpeg`, 258 `.mov`...).
- Files whose name matches `-WA\d`: **0** (only 2 files contain "wa" anywhere in their name, neither
  a WhatsApp name). So: same day 0, name later 0, name earlier 0, no EXIF 0; no median to give.
- Conclusion: the assumption (the name's day is the day received) cannot be checked on this
  collection, which holds no WhatsApp pictures. `classify/received.py` is left unchanged. The
  check can be rerun on a collection that has some (script not kept: ~25 lines, Pillow
  `getexif().get_ifd(0x8769)[0x9003]` against the `YYYYMMDD` of the name).
