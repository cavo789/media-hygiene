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

## Status — PARTIAL (2026-10-24)

### Done
- The large view of the people page sets its one photo aside: a button *Set this photo aside
  (Delete)*, Delete, and Backspace to take it back (the same keys as the shared large view);
  saved in `chosen` like `POST /api/aside` (`remember: false`), read back, the sentence shown
  in the view; the photo then leaves its section (0327). Integration test
  `test_one_photo_set_aside_from_the_large_view_leaves_its_section`; checked in headless
  Chromium with a mocked API (no page error).
- Deviation: the people page keeps its own large view (`#viewer`) with the shared keys, not the
  `pick_viewer` templates: they need the grid state of a page of photos to pick
  (`pick_grid.js.j2`), which the people page is not (it is still exempt from the frame).

### Not done
- "It is the person set aside on <date>" in the people page's large view.
  **Reason:** the large view opens from a face of a section, i.e. the face of *another* person
  (the one of the section); the person set aside is precisely the face not detected. Joining
  the face shown would teach the wrong face. The need is covered by 0351 instead: `/person`
  (👤 from any page, or the photo's path pasted) lets the user choose the right face, finds a
  missed one by a second look (the photo turned), and joins the person set aside before by
  likeness (*the person set aside on <date>*). Close this item unless the maintainer still
  wants it on the people page (then: choose among the faces of the photo, not the one clicked).
