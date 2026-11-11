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

## Status — PARTIAL (2026-11-11)

### Done

- `review/templates/view_state.html.j2`: `window.mhView.get(keys)` (only the page's keys, each
  checked: `int`, `word`, `text` ≤ 200 characters, or a list) and `mhView.set(values, {push,
  state, hash})`; included once, in the head, by the frame, the home page and the album page
  (`test_pick_pages`, `tests/unit/test_view_state.py`). No other template calls
  `pushState`/`replaceState` (tested).
- The large view (`pick_viewer.js.j2`, every page of tiles): opening pushes a step; Back closes it
  as Esc, the grid untouched; ← → replace nothing. The album page's own viewer goes through the
  helper too.
- The library: words, period and folder (the existing `folder_query` key) in the URL, so a reload
  or a bookmark gives the same search; Back from the large view no longer reruns the search.
- Reviews of bursts, near duplicates and pairs: the group shown is the `g` key (its rank,
  replaced at each move), read back on load.
- `home.js.j2`, `home_run.js.j2`, `album.js.j2`, `search.js.j2` moved onto the helper.
- CI browser check: `tests/support/view_walk.py` (reload → same group; large view, Back → closed,
  same scroll; hostile query string dropped), run by `tests/e2e/test_ask_dialog_browser.py`.

### Not done

- View keys of junk, gone, intruders, people, places, quarantine, shrink (their tab/filter):
  the large view's Back works there already (shared viewer), not the reload of a filter.
- A walk per page of `pages_walk.py` in Chromium: the CI check covers the shared helper and
  viewer on one page only.
- Other templates still read `URLSearchParams(location.search)` directly (person, quarantine,
  album_edit, disk space…): reading only, left as is.
