# 0320 — `review --junk` picks its photos as `browse` does (shared `pick_*` templates)

- **Priority**: Medium
- **Batch**: review-ui
- **Depends**: 0319, 0333
- **Files**: `src/media_hygiene/review/templates/unwanted_review.html.j2`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/review/templates/pick_keys.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/review.md`, `documentation/fr/commands/review.md`, `tests/integration/tags/test_pick_pages.py`

## Why

Counted in 0314: `review --junk` shows the photos of a group as tiles (`#shots`) and sets aside
with Space and →, but has no picking gesture (Shift, Ctrl, rectangle, Ctrl+A, I invert), no ⌨
panel at the bottom left, no large view, no *Apply now*. The maintainer's rule (skill
`photo-picking-pages`): one way to pick on every page of tiles.

## What

As 0319, on the photos of the group shown: the shared grid, rectangle, large view and keys
panel; a pick is set aside with Delete or the bar's button, as on `browse`. Add *Apply now*
(`apply_now.html.j2`) when opened from the home page.

## Tests

The page in `test_pick_pages.py`; its existing tests green.


## Decided (2026-10-27)

- Next/previous series stay on ←/→/Space as today; on this page the grid frame moves with ↑/↓ only (maintainer).
- Delete sets the picked shots aside (1…9 removed); A adds to the album in the large view as in browse, "keep all" becomes a button (maintainer).
- 0321: the shared grid script gets an option that turns its picking keys off, so one large view serves every page (maintainer).
