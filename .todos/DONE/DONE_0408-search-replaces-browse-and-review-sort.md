# 0408 — search replaces browse and review-sort: heaviest files and bit rate first, then retire them

- **Priority**: High
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/search/templates/search_folders.js.j2`, `src/media_hygiene/search/templates/pick_order.html.j2`, `src/media_hygiene/search/heaviest.py`, `src/media_hygiene/search/statements.py`, `src/media_hygiene/search/fts.py`, `src/media_hygiene/review/templates/pick_views.html.j2`, `src/media_hygiene/cli/cmd_browse.py`, `src/media_hygiene/cli/cmd_review_sort.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/`, `documentation/fr/commands/`

## Why

Decided by the maintainer on 2026-10-26 (0348 follow-up): the search page replaces `browse` and
`review-sort`. Before retiring them, the search must offer what only they have, so nothing is lost.

## What to do

1. **Heaviest files** in the search: *⚖ Heaviest files* above the tree of *In a folder* (as on the
   folder view), the videos first unless *Show* says otherwise, *Show more*; reuse `heaviest.py`.
2. **Sort by: bit rate** in the search (`pick_order.html.j2`, `order_rate` on the search too): the
   videos worst compressed for their length first, server side before the limit.
3. Then retire `browse`: `mh browse` opens the search on the folder tree (an alias, said once),
   links moved (home page, *Apply now*, menu catalog, docs, mkdocs nav, `pick_views` tabs gone).
4. `review-sort`: list what it has that the search lacks (events one at a time, *Sort this event
   now*, the workbook overlay, the progress line) in the feedback, bring what matters, then retire
   it the same way — ask the maintainer before removing anything that has no equivalent.
5. Load the `photo-picking-pages` skill first; check in headless Chromium; both doc languages;
   `docs_screenshots` must then run (do not run it here).

## Tests

- Heaviest files and bit rate on the search give the same first files as on the folder view
  (equivalence on the same index).
- `mh browse` still works (alias); no link to `/browse` left in pages, docs, menu catalog.

## Status — PARTIAL (2026-10-26)

### Done
- Heaviest files, *Sort by: bit rate*, *Show more* and the video facts on the search page;
  equivalence test with the folder view's heaviest list.
- `browse` an alias: `/browse` is the search page with its folders open; tabs gone; help and menu
  texts; docs (both languages).

### Not done
- Removing the dead folder-view code (`browse.html.j2`, `browse.js.j2`, `/api/folder`,
  `/api/heaviest`, their tests) and updating the docs-screenshot scenario (`tests/support/docs/`).
  **Reason:** the scenario needs a `docs_screenshots` run to be checked, not run in this session.
- Retiring `review-sort`.
  **Reason:** the maintainer decides which of its features (events one at a time, the event card,
  *Sort this event now*, *Remember as a rule*, the plan's progress and runs, the workbook overlay)
  must come to the search first.

## Inbox (2026-10-27)

- Retiring `review-sort`: everything comes to the search first, as a third view *🗂 Events* (events one at a time with filters and progress, the event card Folder / Name / destination, *Sort this event now* M, *Remember as a rule* R, the workbook overlay and its conflicts); `mh review-sort` then an alias of that view, as `browse`. Lost: Delete taking back a choice (it sets aside everywhere). The dead folder-view code goes in the same follow-up. → 0415; closed to DONE (maintainer, 2026-10-27).
