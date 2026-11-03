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
- [ ] New photos: the page opens at once, their analysis followed in it
