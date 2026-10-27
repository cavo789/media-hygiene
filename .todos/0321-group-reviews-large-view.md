# 0321 — The large view on the reviews that answer per group (`--near`, `--gone`, `--pairs`)

- **Priority**: Low
- **Batch**: review-ui
- **Depends**: 0319, 0333
- **Files**: `src/media_hygiene/review/templates/near_review.html.j2`, `src/media_hygiene/review/templates/gone_review.html.j2`, `src/media_hygiene/review/templates/pairs_review.html.j2`, `src/media_hygiene/review/templates/pick_viewer.js.j2`, `src/media_hygiene/review/templates/pick_viewer.html.j2`, `documentation/en/commands/review.md`, `documentation/fr/commands/review.md`

## Why

Counted in 0314: these pages answer one group at a time (keep/leave, deleted on purpose/moved,
a folder pair), so the picking gestures do not apply; but none has the large view of `browse`
(double click or Enter, ← →, F full screen, Esc), and `--gone`/`--pairs` have no ⌨ panel.
The maintainer, 2026-10-23: "on `browse` I double-click a photo to see it full screen".

## What

First check, per page, which tiles are photos worth seeing large (a pair of folders may show
none). Where they are: `pick_viewer.*` on those tiles, its picking keys left out (`pick_marks =
false`), and the ⌨ panel where missing (0304's style). Skill `photo-picking-pages`.


## Decided (2026-10-27)

- Next/previous series stay on ←/→/Space as today; on this page the grid frame moves with ↑/↓ only (maintainer).
- Delete sets the picked shots aside (1…9 removed); A adds to the album in the large view as in browse, "keep all" becomes a button (maintainer).
- 0321: the shared grid script gets an option that turns its picking keys off, so one large view serves every page (maintainer).
