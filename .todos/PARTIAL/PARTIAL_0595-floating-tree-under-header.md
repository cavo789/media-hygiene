# 0595 — Search: the first ⋯ of the floating folder tree lies under the page's header; empty Events buttons

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: —
- **Files**: `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search_events.js.j2`

## Seen (measured in headless Chromium, demo tree, 2026-11-05, during 0533)

- `#folders[open] > #tree` is `position: fixed; top: 16px`: `mh-shell-top` intercepts the clicks on the
  first folder's ⋯ (Playwright's click refused 30 s). Its *Role of this folder* cannot be reached.
- On the 🗂 Events tab with no classify plan: an empty brown button (`#sure`) and *Not saved (error
  404)* in `#eventsSaid`.

## Done when

Both gone, driven in a browser.

## Status — PARTIAL (2026-11-06)

### Done
- `#folders[open] > #tree` now starts at `calc(var(--mh-shell-top-h, 0px) + 16px)` (its
  height shortened as much): the shell's sticky header (57 px, z-index 20) no longer covers
  the first folder's ⋯.
- `#sure` is `hidden` in the markup until `showSure` gives it a text: never an empty button.
- The Events list failing to load says *The events could not be read (error N)*, no longer
  *Not saved (error N)* (a save text for a read). FR translated.

### Not done
- Driving it in a browser (the *Done when*). **Reason:** no Chromium in the devcontainer and
  the Playwright image (`tests/support/pages_browser.py`) is not built here; a 2 GB pull was
  not run under the light-load rule. Also the 404 itself was not reproduced: since 0572 the tab
  lists the index's events (`SpanEvents`, always present) and hides `.eventButtons`; the 404 of
  2026-11-05 may predate that. Check: open the search on the demo tree, open the folder tree,
  click the first ⋯; open 🗂 Events with no classify plan.
