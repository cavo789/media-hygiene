# 0642 — Pick all N found works with the place filter, narrowed by the server

- **Priority**: Low
- **Batch**: library
- **Depends**: —
- **Files**: `src/media_hygiene/search/album_filter.py`, `src/media_hygiene/search/templates/search.js.j2`

## Problem

Follows 0602 (commit 08b2bf12). *Pick all N found* follows the album filter; with the place filter
it is still hidden, since that filter is not applied by the server on the "all" re-runs.

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06 (2))

Same as the album filter: narrowed by the server, the button shown.

## Acceptance

- [ ] Place filter on: *Pick all* picks exactly the files shown (integration test)
