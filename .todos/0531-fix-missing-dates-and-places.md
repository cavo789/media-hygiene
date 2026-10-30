# 0531 — Photos without a date or a place: fix them by group, seen

- **Priority**: Medium
- **Batch**: search
- **Depends**: 0524
- **Files**: `src/media_hygiene/search/`, `src/media_hygiene/services/xmp.py`, `src/media_hygiene/services/xmp_plan.py`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`

## Asked (maintainer, 2026-10-30)

UX brainstorm: give a date or a place to a whole group seen on screen, not photo by photo.

## What

- In `search`, a quick filter "Without a date" / "Without a place" (index facts).
- Results grouped by folder, then by burst or close names; pick a group (or tiles),
  *Set the date…* (proposed: the folder name's date, the neighbours' dates) / *Set the
  place…* (the places list, the map).
- Written as XMP sidecars (the existing `xmp` route), never into the originals; undoable.
- To check first: what `mh xmp` already writes, and whether search reads sidecars back.

## Done when

A date set on a group is read back from its sidecars and shown on the tiles; the filter
count drops (test).
