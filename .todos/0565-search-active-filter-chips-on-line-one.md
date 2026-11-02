# 0565 — Search: the active filters as removable chips, next to the count

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/search/templates/search.css.j2`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

Item 6 of 0463 **barre compacte de la page de recherche** (PARTIAL). The maintainer chose on
2026-11-02, in the review of `feedback-2026-10-29-iterate-2.md`, where the chips go: on line 1 of
the bar, next to the count. The bar stays at 2 lines.

## What

- Each active filter (year, person, place, folder, words…) is a small chip with ✕ on line 1 of the
  bar, after the count. ✕ removes that filter and searches again.
- Too many chips for the width: the extra ones fold into `+N` (a click shows them). The bar
  never grows and the grid never moves (skill `photo-picking-pages`).
- Docs en + fr; `docs_screenshots` should run.
