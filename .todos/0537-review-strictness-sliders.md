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
