# 0666 — Every page keeps its view in the URL: Back, reload and a bookmark work

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/page_frame.html.j2`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/review/templates/pick_viewer.js.j2`, `src/media_hygiene/review/templates/review_board.js.j2`, `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/places/templates/places.html.j2`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

In a web application the browser's Back button, a reload and a bookmark bring back what was
on screen. *Measured* (`grep pushState|replaceState|popstate` over the templates,
2026-11-10): only 4 templates touch the history (`search.js.j2`, `home.js.j2`,
`home_run.js.j2`, `album.js.j2`). On the other pages (reviews of bursts, near duplicates,
pairs, junk, people, places, quarantine, shrink) a reload or Back loses the group shown, the
filter, the large view opened.

## Proposal

- A shared helper in the frame: `mhView.get()` / `mhView.set({...}, {push})` over the query
  string; each page declares the few keys that make its view (tab, filter, group or folder,
  photo opened).
- Opening the large view **pushes** an entry: Back closes it (as Esc), instead of leaving
  the page. Moving inside a list **replaces** it.
- A link copied to another tab of the same PC opens the same view; on a phone too (reads).
- Never a path of a photo in the URL: the keys the pages already use.

## Acceptance

- [ ] Each page of `tests/support/pages_walk.py`: open a view, reload → same view; open the
      large view, Back → the grid, same scroll (headless Chromium)
- [ ] The helper is in the shared templates only

## Where the user gains

Before: 4 templates of about 20 pages keep their view (measured). After: all; Back never
throws the user out of a review they were in the middle of.
