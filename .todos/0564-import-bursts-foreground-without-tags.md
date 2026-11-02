# 0564 — Import chain: the burst page in the foreground when tags are off

- **Priority**: Low
- **Batch**: import
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/services/import_bursts.py`, `documentation/en/`, `documentation/fr/`

## Why

Review of `feedback-2026-10-29-iterate-3.md` (TODO 0480, maintainer's answer 2026-11-02): the
burst page runs detached so tags can run beside it. When `tags` is off in `[imports] then`,
nothing runs beside it: the detached container, *Press Enter* and `docker stop` are useless steps.

## What

- When the chain holds `bursts` but not `tags`: run the import's burst review in the foreground
  (the page closes → the chain goes on with `clean --decisions import-bursts.json`), no
  *Press Enter* question.
- With `tags` on: unchanged (detached).
- Docs en + fr where the chain is described; `docs_screenshots` should run.
