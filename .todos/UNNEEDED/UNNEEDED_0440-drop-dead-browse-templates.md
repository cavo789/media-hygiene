# 0440 — drop the dead browse templates, keep *⚖ Heaviest files* (4/4 of 0415)

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/search/templates/browse.js.j2`, `src/media_hygiene/search/folders.py`

## Why

Part 4 of 0415 (split 2026-10-27). The 0415 run found its point 4 partly wrong: `/api/heaviest`
is still used by search's *⚖ Heaviest files* (`search.html.j2:181`, `search_folders.js.j2:28`):
keep it. Only `browse.html.j2` / `browse.js.j2`, and maybe `POST /api/folder`, look dead: prove
each unused (grep, tests) before removing.

## Explicit NON-goals

- `/api/heaviest`.

## Status — UNNEEDED (2026-10-29)

Checked before removing anything: `browse.html.j2` / `browse.js.j2` are not dead. `mh browse`
(`cli/cmd_browse.py`, `command_functions.py`) is a documented verb (`documentation/*/commands/browse.md`);
`services/search_app.py` still renders `browse.html.j2` (`_BROWSE_TEMPLATE`) and serves `BROWSE_PATH`
(`/browse`, `search/app.py`, `lan_paths.py` phone pages, `step_watch.py`, the launcher's relayed pages,
`tests/unit/test_page_frame.py`, `tests/support/page_render.py`, docs screenshots). `browse.js.j2` calls
`/api/folder` (`FOLDER_PATH`, `browse.js.j2:67`). Removing them would break a live verb: the premise
("0408 left dead code") no longer holds. Reopen only with a decision to retire `mh browse` itself.
