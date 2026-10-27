# 0439 — retire `review-sort` once search's *🗂 Events* does it all (3/4 of 0415)

- **Priority**: Medium
- **Batch**: search
- **Depends**: 0438
- **Files**: `src/media_hygiene/review/sort_*.py`, `src/media_hygiene/cli/cmd_review_sort.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/`, `documentation/fr/commands/`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`

## Why

Part 3 of 0415 (split 2026-10-27; design in `.todos/UNNEEDED/UNNEEDED_0415-*.md`): `review-sort`
opens search's Events view for one version (a one-line notice), then its code, page, docs,
catalog entry and nav go. An existing `sort-decisions.json` keeps working.

## Explicit NON-goals

- The browse templates (0440).
