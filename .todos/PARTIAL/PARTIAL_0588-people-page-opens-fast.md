# 0588 — `mh people` from the home page opens in seconds, not 32 s

- **Priority**: High
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/faces/`, `src/media_hygiene/services/people*`, `src/media_hygiene/index/`

## Measured (maintainer, 2026-11-03, Windows, from 0583)

From the click on the home page to the page: **32.1 s** (stopwatch). The console: about 100 new
photos analysed at 0.16 s each (≈ 17 s, *computed*), then the grouping of all the faces of the
library (≈ 20 000) redone at every opening; the rest ≈ 15 s (*estimated* by difference).

## To do

1. Measure here first (`measure-before-ranking`, a synthetic index of 20 000 faces, `py-spy`):
   container start, analysis, grouping, page start.
2. Keep the groups in the cache; regroup only the new faces.
3. Open the page first; analyse the new photos in it, with their progress.
4. The maintainer times it again after the change.

## Acceptance

- [ ] With no new photo: the page in under 3 s (measured on Windows)
- [x] New photos: the page opens at once, their analysis followed in it
  → driven in Chromium by `tests/e2e/test_people_new_photos_browser.py` (0756, 2026-11-13)

## Status — PARTIAL (2026-11-06)

### Done
- Measured here: synthetic index, 20 000 faces and photos, `nice`, 4 CPUs: listing 0.25 s, grouping 4.7–5.5 s (`_graph` 5.1 s, whispers 0.6 s), the rest of the page 0.1 s.
- Groups kept in the index (`index/face_groups`, version 18), by a digest of each vector: nothing to regroup when no face is new; a few new faces join (`join_labels`); past a tenth joined, all regrouped.
- The step *people* of the home page opens `/people/` at once past the first run, up to 1 000 new photos; the page analyses them through `/api/people`, with its count and Stop.

### Not done
- Item 4 and both acceptance lines: timing on Windows, and the page's script driven in a real browser.
  **Reason:** needs the maintainer's machine; container start and the 15 s "rest" cannot be measured here.
