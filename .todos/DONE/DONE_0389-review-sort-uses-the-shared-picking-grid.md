# 0389 — review-sort picks its photos as `browse` does (shared `pick_*` templates), with ← → between events

- **Priority**: Medium
- **Batch**: review-ui
- **Depends**: 0387
- **Files**: `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/review/templates/pick_viewer.js.j2`, `src/media_hygiene/review/templates/pick_band.js.j2`, `src/media_hygiene/review/templates/pick_keys.html.j2`, `src/media_hygiene/review/sort_app.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/review-sort.md`, `documentation/fr/commands/review-sort.md`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`, `tests/integration/tags/test_pick_pages.py`

## Why

The maintainer on `mh review-sort`, 2026-10-25: "the page does not follow our template. What
must I do? Select photos? I should then have our buttons select / invert, our checkboxes, the
rectangle, Ctrl-click and Shift-click." Read in the template: `sort_review.html.j2` extends
`page_frame.html.j2` but includes none of the `pick_*` parts; it has its own Space / O / S keys
and its own zoom (Z). Same gap as `review` (0319).

Also asked: "Event 1 of 1137" with ← and → buttons to go from one event to the next (today only
the keys N / P, not shown on the page).

## What

Load the skill `photo-picking-pages` first.

- The photos of the event shown are the grid, from the shared `pick_*` templates with the hooks
  of a page whose pick means something else (`saveChoice`, `pick_add`/`pick_remove`: *Send to
  another category* (O), *Leave where they are* (S)); every gesture of the skill's table.
- The large view replaces Z (Enter, double click; Z can stay as an alias only if the skill allows).
- The bar starts with **← Event 1 of 1137 →** (buttons for P / N), keeping the grid still.
- The event-to-event keys (Enter, N, P, U, V, E, C, Shift+S, Delete for a choice) stay, listed in
  the same ⌨ panel; Delete keeps its meaning in the skill (set aside → here: take back the
  choice) — check against the skill, never two meanings.

## Tests

The page in `test_pick_pages.py`; gestures in headless Chromium (skill checklist); its existing
tests green. Say that `docs_screenshots` should run.
