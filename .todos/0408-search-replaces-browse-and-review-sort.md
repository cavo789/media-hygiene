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
