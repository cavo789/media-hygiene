# 0415 — search: an *🗂 Events* view takes in review-sort, then retire it

- **Priority**: High
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/review/templates/pick_views.html.j2`, `src/media_hygiene/review/sort_app.py`, `src/media_hygiene/review/sort_session.py`, `src/media_hygiene/review/sort_views.py`, `src/media_hygiene/review/sort_now.py`, `src/media_hygiene/review/sort_rule.py`, `src/media_hygiene/cli/cmd_review_sort.py`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/search/templates/browse.js.j2`, `src/media_hygiene/cli/menu_catalog_*.py`, `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/`, `documentation/fr/commands/`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`

## Why

Decided by the maintainer (inbox, 2026-10-27; follows 0408, 0399): the search page replaces
`review-sort` as it replaced `browse`; **everything** review-sort has comes first.

## What

1. A third view *🗂 Events* in the search's left column (the latest classify run): the events one at
   a time with their 3 filters and the progress (0398), the event card (Folder / Name / live
   destination), *Sort this event now* (M, 0390/0397), *Remember as a rule* (R) and *Your rules*
   (0392–0395), the workbook overlay and its conflicts banner. The grid and bar stay the shared
   `pick_*` ones (skill `photo-picking-pages` first).
2. Keys: review-sort's O / S / V / Shift+Z / U / N kept where they do not clash; **Delete sets
   aside everywhere** (review-sort's "take back a choice" moves to another key, listed in the ⌨
   panel) — the one loss accepted by the maintainer.
3. Then `mh review-sort` opens that view (an alias, as `browse`); links moved (home page, menu
   catalog, docs, mkdocs nav); `review/sort_app.py` and its templates removed.
4. Same lot: remove the dead folder-view code left by 0408 (`browse.html.j2`, `browse.js.j2`,
   `/api/folder`, `/api/heaviest`, their tests) and update the docs-screenshot scenario.

## Tests

The sort-review integration tests run against the view; `sort-decisions.json` written as before
(same format, NON-goal: no change to classify/sort files); old routes redirect; no link to
`/review-sort` or `/browse` left. Say that `docs_screenshots` must run.
