# 0594 — Page steps served by the home server: no restart, no port race

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: 0494 (DONE)
- **Files**: `src/media_hygiene/services/home_pages.py`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`

## Why (0513, cause 1)

The 13 `PAGE` steps but `search` still end the home server and start a container of their own.

## What

Per page: what it needs that the home server lacks (its session state, a mount, an option), then
serve those that can be, as `search`, `/disk-space/` are. A study first; one child per page.

## Done when

The table page → blocker is in this TODO, and every page without a blocker is served there.
