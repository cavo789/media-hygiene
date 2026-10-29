# 0457 — search: *🗂 Events* as a tab, not a collapsible section

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/`, `src/media_hygiene/search/events_desk.py`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Why

The maintainer, 2026-10-29 (inbox, 0446 question 1): the events of search belong in a tab of
their own (*Photos* / *Events*) rather than a collapsible section under the grid.

## What

Two tabs at the top of the search page; the chosen tab kept per viewer (`localStorage`, wrapped
in try/catch). Layout from the shared `pick_*` templates (skill `photo-picking-pages`).

## Acceptance

- Both tabs reachable by mouse and keyboard; the Events choices (and key T) unchanged.
- Docs en + fr; `docs_screenshots` to run.
