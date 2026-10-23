# 0327 — People page: the photos set aside are no longer shown among the faces

- **Priority**: Medium
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/people/views.py`, `src/media_hygiene/people/sections.py`, `src/media_hygiene/people/roster.py`, `src/media_hygiene/people/templates/people.html.j2`, `tests/integration/people/test_people_aside.py`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

## Why

The maintainer, 2026-10-23, on `mh people`: the section "Manon (attributed) — 2548 faces in
2530 photos" said "1 of these photos is set aside" — they do not want to see again the photos
they decided to remove. Checked that day (read-only, `docker exec` on the running `people`
container): `/reports/decisions.json` held 10 photos chosen from `search` (5 `caption`, 5
`vision`, `C:\Photos\Manon 2023\dcim` and `C:\Photos\2023\Juillet 2023\Crête`), not yet moved
by `clean --decisions`; the 140 photos set aside on the people page the day before were
applied at 12:23 (`decisions.applied-20261023-122322.json`) and are already gone from the page:
`clean` parks their index rows, faces included (`index/parked.py`). So only the photos *set
aside and waiting* still show; they are counted and drawn like any other.

## What

- A face whose photo is in the decisions file (`chosen`, any page that put it there: search,
  browse, phone, people) is left out of the sections: not drawn, not counted in "n faces in
  m photos", not used to attribute or suggest a name (0326), never confirmed by "Yes, these
  are X". The section line says instead "1 photo set aside, hidden — Show / Take back".
- "Show" draws them again in that section, dimmed (to take one back); "Take back" keeps its
  current meaning.
- Group computation unchanged (the faces stay in the cache until `clean`): only the page view
  filters, so taking a photo back shows it again without a new analysis.
- Check the other tile pages (browse, search, phone — skill `photo-picking-pages`) for the same
  question and say in the report whether they should hide set-aside photos too (today they
  mark them, to take them back); do not change them in this TODO.

## Tests

- Integration: a photo set aside disappears from its section and its counts; taken back, it
  shows again; "Yes, these are X" never sends a face of a set-aside photo.
- Docs en + fr; captures stale → `docs_screenshots`.
