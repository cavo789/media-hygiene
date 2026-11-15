# 0838 — Large view: outline each face on the photo, names shown on it (on/off switch)

- **Priority**: High
- **Batch**: faces-large-view
- **Depends**: none
- **Files**: `src/media_hygiene/person/shelf.py`, `src/media_hygiene/person/app.py`, `src/media_hygiene/review/templates/pick_who.js.j2`, `src/media_hygiene/review/templates/pick_viewer.html.j2`, `src/media_hygiene/review/templates/pick_viewer.css.j2`, `src/media_hygiene/review/templates/pick_viewer.js.j2`, `src/media_hygiene/review/templates/combo_list.js.j2`, `documentation/en/commands/library.md`, `documentation/fr/commands/library.md`

## Reported (maintainer, 2026-11-15)

A group photo opened large (wedding, ~20 people): the who line under it lists 7 faces as
tiny crops ("? not named", "✓ Valéry"…). Clicking one opens "This face is…", but with a
crop that small the maintainer cannot be sure which person on the photo it is.

## Wanted

1. **Outline the face on the photo**: hovering or clicking a face of the who line draws its
   box on the large picture (and keeps it while the "This face is…" line is open). The
   reverse too: a click on a box on the photo opens the same naming line.
2. **Names on the photo**, with a switch in the view ("Show names" / "Hide names"): each
   face's box with its name under it (✓ confirmed, ≈ guessed, ? not named), remembered per
   viewer (localStorage, try/catch). **On by default** (maintainer, 2026-11-15).
3. On **every** large view (`pick_viewer` → library, browse, person, people, reviews,
   phone read-only: names only, no naming) — skill `photo-picking-pages`, rule
   `feature-follows-its-kind`: list each page checked in the report.

4. **Name list always visible** (maintainer, 2026-11-15): typing "T" in "Who is it?" at the
   bottom of the screen opened the list of known names below the field, off screen. The
   shared `combo_list.js.j2` must measure the room below/above the field and open the list
   above it when below is short (max-height = the room left, scrolls inside), on every page
   that uses it.

## How (from the code, 2026-11-15)

- The index already keeps each face's `FaceBox` (`faces/models.py`: x, y, width, height in
  pixels of the **upright** picture). `/person/api/photo` (`person/app.py`, `face_view` in
  `person/shelf.py`) does not send it: add the box as fractions of the upright picture
  (needs its width/height: from the index's visual facts or the box source), so the page
  places it over the `<img>` whatever its displayed size (an absolutely positioned layer
  sized to the image's rendered rect, recomputed on resize/zoom).
- Hand-drawn faces (0715) have a box too: same treatment.
- Bigger crops in the who line are a cheap extra (S/M from the shared size switch?).

## Done when

Hover/click a chip outlines the right face; the switch shows/hides the names; read-only on
the phone; screenshots stale → say `docs_screenshots` should run; both languages updated.
