# 0725 — Photos to straighten: audit caching, page with Apply now, lossless journaled write

- **Priority**: Medium
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/faces/straighten.py`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/scan/visual.py`, `src/media_hygiene/actions/xmp_write.py`, `src/media_hygiene/review/templates/pick_grid.js.j2`

Follows PARTIAL 0711 (`.todos/PARTIAL/PARTIAL_0711-detect-photos-needing-rotation.md`, commit d8c3af65), which shipped only the pure guess (`faces/straighten.py`). PARTIAL 0711 does not carry the remainder as a fresh TODO, so this is it.

Decided by the maintainer in the review of 2026-11-12. (a PARTIAL's remainder becomes a fresh TODO).

## What

- Call the guess in the audit worker and cache it (index schema bump; a new mtime after a turn = a new row; a refusal kept by path follows `sort`, `undo` and renames).
- The *Photos to straighten* page on the shared `pick_*` templates (skill `photo-picking-pages`), with *Apply now*, the way back home, 🤖 flag where the YuNet guess is pasted.
- A journaled lossless orientation-tag write (no re-encode), `undo` proven byte-identical.
- The audit's *What next* line, a home card, documentation EN + FR (and `docs_screenshots` to run).

## Acceptance

- [ ] Audit twice: the second reads the cache (test).
- [ ] Apply then undo: file byte-identical to before.
- [ ] Refusals survive `sort`/`undo`/rename (tests).
- [ ] Docs EN + FR; French strings.

## Decided (2026-11-13)

The rotation guess is computed in `people` (which already decodes each photo for its faces) and cached there, in the index; the audit runs no face detection (choice by the maintainer, review of `.claude/plans/feedback-2026-11-13-iterate.md`).
