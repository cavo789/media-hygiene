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

## Status — PARTIAL (2026-11-08)

### Done
- The burst series review (`review.html.j2`, the only review page with an albums API) renders 📺
  (`services/review_file.py`, `_TV_PAGES`; hidden until `/api/tv-paired` says a TV is paired);
  served by the home server, its albums desk gets the home server's `TvSlot`
  (`services/review_here.on_tv`): picked files, or nothing picked → the page's files, as on search.
- "Replaced" told on the remote: `Desk.replaced` = (files of the selection, the show's version),
  set by `SlideshowHere._begin` only when a selection of files replaced a running show; the
  remote shows "replaced by a selection of N files" once per show (`#replaced`,
  sessionStorage-marked by the show's version). The pages' bar now only says "Sent to the TV".
- Tests in `tests/unit/test_tv_selection.py`; docs en/fr `commands/slideshow.md`.
  `docs_screenshots` is stale for the slideshow remote and the burst review.

### Not done
- 📺 on the other review pages with tiles (`unwanted_review`, `quarantine`, `import_pick`), on
  `/person` and on the phone page.
  **Reason:** none of them has an albums API: each needs its own `action: "tv"` endpoint whose
  picker turns the page's keys into files of the index (never a path from the request), and the
  `TvSlot` carried to `person/door.py` (served by many servers, not only the home server) and to
  the phone page's server. A design per page, larger than this lot; the near review has no
  picking bar.
