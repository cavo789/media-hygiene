# 0566 — Places map: a merged town shows a few photos of each folder

- **Priority**: Low
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/places/clusters.py`, `src/media_hygiene/places/tree_rows.py`, `src/media_hygiene/places/drawer_rows.py`, `src/media_hygiene/places/templates/`

## Why

Question of 0383 **dossiers d'une même ville fusionnés en un repère** (review of
`feedback-2026-10-27-iterate.md`, 2026-11-02). Today the drawer shows the first `MEMBERS_KEPT`
photos across all folders, the biggest folder first: a small outing in the same town is
invisible. Maintainer: show a few photos of each folder.

## What

- The drawer of a merged group: one short row per folder (its name + its first 3–4 photos),
  biggest folder first, with the same total cap as today (no slower page).
- Test: a group of 3 folders of 50, 5 and 2 photos shows all three.
