# 0525 — Visual quarantine: restore picked photos from a grid

- **Priority**: Low
- **Batch**: review
- **Depends**: —
- **Files**: `src/media_hygiene/actions/`, `src/media_hygiene/services/undo.py`, `src/media_hygiene/services/quarantines.py`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/cli/menu_catalog_clean.py`

## Asked (maintainer, 2026-10-30)

UX brainstorm: "not convinced but the idea is good: a low TODO if useful".

## What

- A page showing the quarantine (every drive's, `paths/quarantines.py`) as tiles, grouped by run,
  newest first, built on the shared `pick_*` templates (skill `photo-picking-pages`).
- Pick photos, *Restore*: each goes back to its original path through the undo machinery
  (a partial undo of a run, journaled), refused where `undo` refuses (drive not mounted).
- Today `mh undo` takes a whole run back; this restores one photo seen.

## Done when

A restored photo is back at its path, read back from disk; the rest of its run stays in the
quarantine and `mh undo` of that run still works (test).
