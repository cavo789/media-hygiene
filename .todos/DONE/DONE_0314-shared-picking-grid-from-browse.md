# 0314 — One picking grid and one large viewer for every page of tiles: browse's, reused by the phone page

- **Priority**: Medium
- **Batch**: review-ui
- **Depends**: 0312, 0304
- **Files**: `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/review/templates/pick_viewer.js.j2`, `src/media_hygiene/review/templates/phone_review.html.j2`, `src/media_hygiene/review/templates/phone_review.js.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `tests/integration/test_phone_review.py`

## Why

The maintainer, 2026-10-23, on the page of `mh phone --free`: "the same features as `browse`:
the keyboard list at the bottom left, Ctrl/Shift to pick one photo then another, a rectangle
drawn with the mouse, invert the picking… This kind of page should become a reusable model."

Today these gestures live in `browse` only (`browse.js.j2`: `pick()` with Shift/Ctrl, `invert()`,
Ctrl+A, Home/End, arrows + Space; `browse_band.js.j2`: the rectangle; the **⌨ Keyboard**
panel in `browse.html.j2`). 0304 shares the panel's *style*; this TODO shares the *behaviour*.

## What

**Done on 2026-10-23 (outside this TODO, the maintainer's report on `mh search`)**: steps 1 and 3
for `browse` and `search`. The shared templates exist in `review/templates/`: `pick_grid.css.j2`,
`pick_views.html.j2`, `pick_keys.html.j2`, `pick_acting.html.j2`, `pick_viewer.html.j2`,
`pick_grid.js.j2`, `pick_viewer.js.j2`, `pick_band.js.j2` (was `browse_band.js.j2`); the
contract is the skill `photo-picking-pages`. What is left: step 2 (the phone page uses them),
the viewer's Space on the phone page, step 4 (the feature table and the follow-ups).


1. **Extract** from `browse` a template script (`pick_grid.js.j2`, included like
   `browse_band.js.j2`) that owns: the set of picked tiles, click / Ctrl+click / Shift+click,
   the rectangle, Ctrl+A (per group: the folder in view), I (invert), arrows + Space, Home/End,
   and the panel's common keys. The page gives it its tiles (DOM nodes + keys) and a callback
   `onChange(changes)`. `browse` uses it with no visible change (its tests stay green).
2. **The phone page uses it**, on the folder groups of 0312. Its ☑ is the tick itself
   (ticked = leaves the phone), so a gesture changes ticks directly, sent in one
   `POST /api/phone` per gesture, read back from the disk as today.
   - A set-aside file is never ticked by a bulk gesture (rectangle, Ctrl+A, invert, Shift):
     only by its own box, with its confirmation (`confirmAside`); the status line says "N set
     aside left unticked".
   - The ⌨ panel at the bottom left lists the phone page's keys; no `Delete` key there (the
     only deletion is the page's button).
3. **The large viewer** (maintainer, 2026-10-23: "on `browse` I double-click a photo to see it
   full screen; not on `mh phone`"). `browse` and `search` each carry their own viewer today
   (`#viewer` in `browse.html.j2`, a `dblclick` in `search.html.j2` too — counted with `grep -rln
   dblclick`). Extract it next to the grid (`pick_viewer.js.j2` + its CSS): double-click or
   Enter opens the tile large, ←/→ the previous/next one, F full screen, Esc closes, its keys
   in the panel. The phone page uses it on the PC's copy (the `/original/` route of
   `review/files.py`, reached through `PhoneSession.preview_source` — to check that it answers
   for the phone's keys); in the viewer, Space ticks or unticks the file shown (the same rule
   for set-aside files).
4. **The same features on every page of tiles** — the maintainer's rule, 2026-10-23: "make
   sure our pages offer the same features". Write a table in the commit: each page of tiles
   (`browse`, `search`, phone, `review --junk`, `review --gone`, `review --near`, bursts — to
   check which are grids) × each feature (picking gestures, rectangle, invert, ⌨ panel, large
   viewer, full screen, Apply now). Convert here only `browse` (extraction) and the phone page;
   file one follow-up per other page that lacks a feature, naming the shared templates.

`src/` files stay under 200 lines (`.claude/scripts/near_limit.sh` before writing):
`browse.js.j2` is 469 lines today (counted `wc -l`), so the extraction also shrinks it.

## Tests

- `browse`: its existing page tests unchanged.
- Phone page: the rendered page holds `id="keys"` and the shared script; an integration test
  sends a multi-file choice as a rectangle would and reads back the file.

## Docs

The launcher page's section on freeing the phone (both languages): the gestures, as written
for `browse`. `docs_screenshots` should run afterwards (not unasked).
