# 0319 — The burst review picks its shots as `browse` does (shared `pick_*` templates)

- **Priority**: Medium
- **Batch**: review-ui
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/review/templates/pick_viewer.js.j2`, `src/media_hygiene/review/templates/pick_band.js.j2`, `src/media_hygiene/review/templates/pick_keys.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/review.md`, `documentation/fr/commands/review.md`, `tests/integration/tags/test_pick_pages.py`

## Why

The maintainer's rule, 2026-10-23: every page of tiles offers the same features (skill
`photo-picking-pages`). Counted in 0314 (`grep` of the page and its scripts): `review` (burst
series) shows the shots of a series as tiles but has none of the picking gestures (Shift, Ctrl,
rectangle, Ctrl+A, I invert), no large view (double click, Enter, ← →, F full screen) — only its
own keys and its ⌨ panel, and *Apply now*.

## What

Load the skill `photo-picking-pages` first. The shots of the series shown are the grid: build it
from `pick_grid.js.j2`, `pick_band.js.j2`, `pick_viewer.js.j2` and their HTML/CSS, with the hooks
0314 added for a page whose pick means something else (`saveChoice`, `placeCards`,
`deleteKeySets`, the `pick_add`/`pick_remove`/`pick_marks`/`pick_space` variables). Keep the
series-to-series keys the page has today; list them in the same ⌨ panel.

## Tests

The page in `test_pick_pages.py` (each shared part once); its existing tests green.

## Explicit NON-goals

The near-duplicate, pairs and gone reviews (0321).
