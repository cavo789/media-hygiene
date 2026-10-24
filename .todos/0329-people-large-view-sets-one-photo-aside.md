# 0329 — People page: the large view sets one photo aside

- **Priority**: Medium
- **Batch**: people
- **Depends**: 0327
- **Files**: `src/media_hygiene/people/aside.py`, `src/media_hygiene/people/app.py`, `src/media_hygiene/people/templates/people.html.j2`, `tests/integration/people/test_people_aside.py`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

## Why

The maintainer, 2026-10-23: a photo shows, in someone's section, a person they set aside the day
before, whose face was not recognised (in profile). On the people page, only a whole section can
be set aside: the large view (`#viewer`) shows the photo and its path, nothing to act on it.
`browse` and `search` can set one photo aside; the people page cannot.

## What

- In the large view, a button "Set this photo aside" (and its key, the same as the shared
  `pick_viewer` large view — skill `photo-picking-pages`: reuse its bar and keys rather than a
  new one), saved in the decisions file like `POST /api/aside` (read back from the disk, the
  sentence shown); the photo then leaves the sections (0327).
- When 0328 is done: setting one photo aside from the large view, while a set-aside face exists,
  offers "It is the person set aside on <date>" — the face of that photo, if one was detected,
  joins that remembered face (better matches next time).

## Tests

- Integration: one photo set aside from the large view lands in `chosen` and leaves its section.
- Docs en + fr; captures stale → `docs_screenshots`.
