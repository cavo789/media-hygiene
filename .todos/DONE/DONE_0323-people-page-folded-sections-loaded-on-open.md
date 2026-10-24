# 0323 — People page: sections fold, verified ones folded by default, faces loaded on opening

- **Priority**: Medium
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/people/views.py`, `src/media_hygiene/people/roster.py`, `src/media_hygiene/people/app.py`, `tests/integration/people/`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

## Why

The maintainer, 2026-10-23, while naming people on `mh people`: the page lists every section
one after the other — each person's *verified* faces, then their *attributed* ones, then the
groups nobody is given — and the verified sections, already done, stand between them and the
work left. They asked to fold and unfold the sections, the verified ones folded by default (or
shown as one line), the photos loaded only when a section is opened, so the page is lighter.

What the page does today (read in the code, 2026-10-23): `GET /api/groups` returns every
section with a sample of up to `SHOWN = 60` faces each (`people/views.py`); the page builds
every section's DOM at once (`render()` in `people.html.j2`); the thumbnails already carry
`loading="lazy"`, so the browser fetches only those near the screen — the weight saved by
folding is the DOM (up to 60 tiles × sections) and the JSON of the samples, not the bytes of
the visible thumbnails. Not measured: to measure on the maintainer's collection (sections
count, JSON size of `/api/groups`, time to first paint) before and after.

## What

- Each section's title is a button (▸ / ▾) folding or unfolding it; keyboard: the current
  section folds/unfolds with a key (e.g. `o` or Space — check against the existing keys
  `j k n y x i` and TODO 0304).
- **Verified** sections folded by default, as **one line**: the name, ✓, the counts, and a
  strip of a few faces (≈ 8, from the sample) so the person is recognised without opening.
  Attributed and unnamed sections open by default.
- A folded section holds no tiles: `/api/groups` sends, for a folded section, only the strip
  (the few faces); opening it asks for its sample (`GET /api/groups/<n>` or the existing
  `expand` route used by "show all"), then draws its tiles. Keep `expand`/"show all" working
  on an opened section.
- What is folded is a per-viewer convenience: remembered in `localStorage` (try/catch, the
  page works without it), keyed by person name + kind (verified/attributed), never by
  section index (indexes shift after each naming).
- After a change (`render(sameSections)`), sections keep their folded state; a section whose
  person just got new verified faces stays as the user left it.
- Moving with `j`/`k` lands on folded sections too (so the user can open one), Enter opens it
  before focusing the name field.

## Tests

- Integration: `/api/groups` sends only the strip for a verified section, the full sample on
  opening; folding state survives a naming; a folded section has no `.face` tiles in the DOM.
- Docs: `commands/people.md` (en + fr) explains folding; captures go stale → `docs_screenshots`.

## Setting?

The strip size (≈ 8) and "verified folded by default" could become `[people]` settings; propose
in the report, default as above.
