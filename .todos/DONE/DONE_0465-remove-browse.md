# 0465 — Remove `browse` (search opened on folders does it)

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_browse.py`, `src/media_hygiene/cli/command_table.py`, `src/media_hygiene/cli/menu_catalog_find.py`, `documentation/en/commands/browse.md`, `documentation/fr/commands/browse.md`, `.config/mkdocs/mkdocs.yml`, `tests/support/docs/scenario.py`

## Why

The maintainer, 2026-10-29: `browse` is already the search page opened on the folders; remove it
to simplify, no hidden alias (as `review-sort`, 0460).

## What

Remove the verb, menu entry, docs pages EN/FR, `nav`, `COMMANDS_TOO`, links; the home page and
`mh` launcher open `search` on the folder tree instead. Changelog line.

## Acceptance

`mh browse` is unknown; `test_docs_commands`, `test_menu_catalog`, `test_docs_site`, `test_documentation` pass.
