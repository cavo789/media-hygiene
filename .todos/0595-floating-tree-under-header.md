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
