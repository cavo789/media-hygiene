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

## Study (2026-11-05, read from `step_watch.SERVED_HERE`, the catalog and each page's flow)

| Page step | What the home server lacked | Blocker | Now |
|---|---|---|---|
| `search` | | | served (0356) |
| `review`, `--near`, `--pairs`, `--junk`, `--gone` | | | served (0357, 0417) |
| `places` | | | served (0417) |
| `slideshow --album … --lan` | | | served (0417, `/slideshow/album/<name>`) |
| `home` | it is the server | | |
| `review --intruders` | its `ReviewKind` | none | **served here**: `/review/intruders/` |
| `undo --pick` | its route | none | **served here**: `/quarantine/` |
| `import --pick` (new, 0590) | its route | none | **served here**: `/import/` |
| `import --pick <folder>` (new, 0590) | the folder's mount | a mount: a plugged-in folder is not in the home container | ends the server, by design |
| `slideshow --folder` | the folder's mount; a filter inside the library would need none | a mount for a folder outside the library | 0598 |
| `shrink --try` | what follows the page: `--apply`'s question and its hours of encoding run in the window | the writing step's own question (0586) | 0599 |
| `people` | finding the faces first: console progress, Ctrl+C, can last hours | a long step before the page | 0600 |
