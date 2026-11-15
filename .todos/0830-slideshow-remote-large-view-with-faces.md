# 0830 — Slideshow remote: a tile opens the large view (faces, → /person, remove a name)

- **Priority**: Medium
- **Batch**: tv-slideshow
- **Depends**: 0829
- **Files**: `src/media_hygiene/slideshow/templates/slideshow.html.j2`, `src/media_hygiene/slideshow/templates/slideshow.js.j2`, `src/media_hygiene/review/templates/pick_large.html.j2`, `src/media_hygiene/review/templates/pick_large_keys.html.j2`, `src/media_hygiene/person/templates/person_names.js.j2`, `src/media_hygiene/slideshow/app.py`, `src/media_hygiene/services/slideshow_build.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Reported (maintainer, 2026-11-15)

The *Avoid some people* block of `/slideshow` listed people the maintainer did not expect
on 2026's photos (André, Evelyne, Fleur…). The ✓/≈ signs now say which ones are only
guessed (≈: a face close to their mean, 0825). To understand and fix a wrong guess, the
maintainer wants what `/library` already does: click a tile → the photo large, its faces
with their names (✓ / ≈ / ?), a way to `/person`, and remove a wrong name.

## What

- Load the `photo-picking-pages` skill first: the large view is the shared one
  (`pick_large*`), with the same faces line and naming part as `/library` (memory
  `reuse-components-always`, `same-features-on-tile-pages`) — never a slideshow copy.
- Today a tile click **jumps the TV** to that photo: keep it (a button *Show on the TV*
  in the large view, or a single click as now and double-click/Enter for the large view,
  as on every tile page — decide with the skill's gestures).
- On the PC: the faces with ✓/≈/?, click a face → `/person` (new tab, the show keeps
  going), *Not this person* removes a guessed name / rejects it as `/person` does (save
  read back from disk). After a change, the *Avoid* block's counts are refreshed
  (`AvoidDesk` finds the people once: give it a way to forget them).
- On a paired phone: read-only (faces and names shown, no naming, no removal).
- The size switch of tiles (S/M/L/XL), like every tile page — check what else the tile
  pages have that this one lacks and list it.

## Tests

- A tile's large view shows its faces' names, from the same shared template as `/library`.
- Removing a guessed name on the PC: the people file read back, the Avoid counts updated.
- Phone: no write control in the large view.
