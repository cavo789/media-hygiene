# 0460 — Remove `review-sort` (search's Events replaces it)

- **Priority**: Medium
- **Batch**: search
- **Depends**: 0457
- **Files**: `src/media_hygiene/cli/cmd_review_sort.py`, `src/media_hygiene/cli/command_table.py`, `src/media_hygiene/cli/menu_catalog_sort.py`, `src/media_hygiene/review/sort_*.py`, `documentation/en/commands/review-sort.md`, `documentation/fr/commands/review-sort.md`, `.config/mkdocs/mkdocs.yml`, `tests/support/docs/scenario.py`

## Why

The maintainer, 2026-10-29 (inbox, 0446 question 5): remove `review-sort` in the next version,
no hidden alias. Its pages, menu entry and site nav go with it.

## What

Check first what `sort` and the carry-over still read from `sort-decisions.json`
(`classify/page_overlay`): keep reading existing files, stop writing them from a removed page.
Remove the verb, its page server, menu catalog entry, docs pages (en + fr), `nav`, `COMMANDS_TOO`,
links from other pages; a changelog/release note line.

## Acceptance

- `mh review-sort` is an unknown command; `sort` still honours an existing `sort-decisions.json`.
- `test_docs_commands`, `test_menu_catalog`, `test_docs_site`, `test_documentation` pass.
