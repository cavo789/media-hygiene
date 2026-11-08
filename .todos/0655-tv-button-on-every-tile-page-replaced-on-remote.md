# 0655 — 📺 *On the TV* on the review pages, `/person` and the phone page; "replaced" told on the remote

- **Priority**: Medium
- **Batch**: tv-slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/review/review_kinds.py`, `src/media_hygiene/review/reviewing.py`, `src/media_hygiene/review/templates/pick_acting.html.j2`, `src/media_hygiene/services/slideshow_selection.py`, `src/media_hygiene/slideshow/`

## Problem

Follows 0454 (PARTIAL). The 📺 button of the shared pick bar is wired on `search` and `browse`
only; the server side (`action: "tv"`) is ready for the others. When a running show is replaced,
the "replaced" line shows in the page's bar, not on the phone's remote.

Decided by the maintainer in the inbox of 2026-11-08: the button on every tile page (same features
at the same place), and the "replaced" line moved to the remote.

## Fix

1. Wire `tv_here` and the albums API resolution on the review pages, `/person` and the phone page
   (load skill `photo-picking-pages`: the shared `pick_*` templates, nothing page-specific).
2. The show's state carries "replaced by a selection of N files"; the remote shows it once
   (the page's bar keeps only its toast that the selection was sent).

## Acceptance

- [ ] 📺 in the bar of each review page, `/person` and the phone page when a TV is paired (tests)
- [ ] Picked files, or nothing picked → the page's files, as on search
- [ ] The remote tells "replaced" after a selection replaced a running show (test)
- [ ] Docs en/fr; `docs_screenshots` flagged stale
