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
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
- [ ] Every key of today still works (headless Chromium, mocked API); *Apply now* and the
  → browser check: CI's job (headless Chromium), not the maintainer's (2026-11-12)
      way back home at the frame's place
- [ ] `docs_screenshots` should run
  → captures: one run of `docs_screenshots`, tracked in 0717 (2026-11-12)

## Where the user gains

Before: 1 of the 20 work pages with its own layout. After: 0; what was learnt on the library
page works on People.

## Status: PARTIAL (2026-11-11)

### Done

- `people.html.j2` extends `page_frame.html.j2` (736 → 147 lines); split into `people.css.j2`
  (64), `people.js.j2` (state, saves, naming, faces: 234), `people_sections.js.j2` (sections,
  keys: 268), `people_viewer.js.j2` (the large view: 110); `people_guide.js.j2` and
  `people_new_photos.js.j2` kept. No file of `people/templates/` above 270 lines.
- Left column: the people list (`#toc`), *Show only this person*, the old header hints in a
  `<details>`, then the ⌨ panel (keys / *More keys* / 🔒). One bar: *To do*, *Next to do*,
  *Only what is left*, *Go to a person*, *Apply now* (the frame's place), the line read back,
  the new-photos line. The frame brings `mhAsk`, `mhSay` (errors also as a toast), `mhView`.
- Large view: the shared markup and look (`pick_viewer.html.j2`, `pick_album = false`), driven
  by `people_viewer.js.j2`; Back closes it (a history step, as 0666). The person chosen is kept
  in the URL (`?who=`), restored on reload when they still exist.
- The exception leaves `tests/unit/test_page_frame.py`; People added to `_MAIN_KEY`;
  `tests/e2e/test_ask_dialog_browser.py` walks People with `view_walk.py` (CI).
- Skill `photo-picking-pages`: the people page's differences written down. Docs EN + FR
  (`commands/people.md`). `docs_screenshots` should run (the page's layout changed).

| Key / action before | After |
|---|---|
| ↑ ↓ / j k, o, Enter / n, y, g, /, x, i | same (panel: ↑ ↓ g Enter y; *More keys*: j k n o x i / Esc) |
| Esc: close the view, else *Show only this person* off | same; the frame's *More keys* closes first when open |
| click a face → its photo; Delete / Backspace in it | same, in the shared large view, + a button for the mouse |
| click on the view closes it | same, + Back, + ← → Home End (faces of the section), F, I (path), ? |
| × / ↺ marks, *Name*, *Yes…*, *Not X…*, *Name with others*, *Ignore*, *Set aside…*, *Show / Hide / Take back*, *It is X?*, *Next to do*, *Only what is left*, *Go to a person*, people list, *Stop* / *Show the new groups*, *Apply now* | unchanged (same ids, same requests) |
| the header's hint lines | in *How it works* (left column) and the ⌨ panel |
| sections loaded on demand (0323), set-aside photos hidden (0327) | unchanged code |

### Not done

- Every key checked in headless Chromium with a mocked API: Playwright is not installed here;
  → browser check: CI's job (headless Chromium), not the maintainer's (2026-11-12)
  only the view walk (URL, Back closes the large view) is added to the CI browser tests.
  `tests/support/pages_walk.py` reaches pages from the home page of a demo tree that has no
  faces: People there needs a face model (🤖) — left out.
- `mhBusy` on the section buttons (a save is short, the bar's *Saving…* line stays): left for
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  a pass over every frame page at once.

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
