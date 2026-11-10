# 0667 — People page onto `page_frame`: the stale exception of the frame test removed

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: —
- **Files**: `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/people/templates/people_guide.js.j2`, `tests/unit/test_page_frame.py`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

*Measured* (2026-11-10): 19 pages `extends "page_frame.html.j2"`; `people.html.j2` (736
lines, its own `<!DOCTYPE html>`) does not. `tests/unit/test_page_frame.py` excuses it as
"temporary: until 0323-0329 are done (they reshape this page)" — 0323 to 0329 are all DONE.
So the page the maintainer's rule targets ("same layout, same buttons at the same place")
still has its own header, keys panel, bar and large view.

## Proposal

- `people.html.j2` extends the frame and fills its blocks; its faces grid uses the shared
  large view (`pick_viewer`) and the keys panel; what is specific (naming a group, verified /
  attributed sections) stays in its own script.
- Load the `photo-picking-pages` skill: faces are tiles that are picked (× marks, set aside).
  Where a gesture differs on purpose, it is written in the skill's "when a page needs
  something else".
- The exception line leaves the test; `album.html.j2` (the phone-first albums page) keeps
  its documented one.

## Acceptance

- [ ] `people.html.j2` extends `page_frame.html.j2`; no exception for it in the test
- [ ] Every key of today still works (headless Chromium, mocked API); *Apply now* and the
      way back home at the frame's place
- [ ] `docs_screenshots` should run

## Where the user gains

Before: 1 of the 20 work pages with its own layout. After: 0; what was learnt on the library
page works on People.
