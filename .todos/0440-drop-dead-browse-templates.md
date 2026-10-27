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
