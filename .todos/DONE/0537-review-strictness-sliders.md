# 0537 — Burst and unwanted reviews: a strictness slider with a live preview

- **Priority**: Medium
- **Batch**: review
- **Depends**: —
- **Files**: `src/media_hygiene/review/shots.py`, `src/media_hygiene/services/unwanted_review.py`, `src/media_hygiene/review/templates/`, `src/media_hygiene/places/toml_edit.py`, `documentation/en/`, `documentation/fr/`

## Asked (maintainer, 2026-10-30)

"If this feature is not shown in the web interface, it is as if it did not exist." Each setting
is placed **on the page where it acts**, next to its visible effect (no catch-all settings page),
saved with `places/toml_edit` (comments kept, atomic) and **read back from disk** before being
shown. Follows 0532 (folder roles); analysed in detail at implementation time.

## Wanted

- Burst page: "more / less strict" over `[review] propose_aside_below` and `identical_below`,
  proposals recomputed live (choices already made kept).
- Unwanted page: per group "too strict?" over `[review.unwanted]` (`tiny_megapixels`,
  `dark_*`, `white_*`, `blur_percentile`, `screenshots`), showing which photos enter or leave.
- Tile pages: load skill `photo-picking-pages`.

## Status — PARTIAL (2026-11-06)

### Done
- Burst page: panel *Too strict? Not enough?* over `propose_aside_below` and `identical_below`; proposals recomputed on letting go, choices kept, shots entering and leaving named.
- Unwanted page: one *too strict?* panel per reason over `screenshots`, `tiny_megapixels`, `dark_*`, `white_*`, `blur_percentile`; a photo already decided stays listed.
- *Keep these values*: `toml_edit`, only the changed keys, read back and shown. Docs in both languages.

### Not done
- Gestures and sliders driven in a real browser, and `docs_screenshots`.
  → browser check: CI's job (headless Chromium), not the maintainer's (2026-11-12)
  **Reason:** no node nor browser run in this unattended lot; rendered HTML and server answers are tested. Run the checklist of skill `photo-picking-pages` once, then `docs_screenshots`.

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
