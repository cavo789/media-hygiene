# 0657 — The phone page and `/person` gain the albums API: ➕ *Add to an album* and 📺 *On the TV*

- **Priority**: Medium
- **Batch**: tv-slideshow
- **Depends**: 0660
- **Files**: `src/media_hygiene/review/`, `src/media_hygiene/people/`, `src/media_hygiene/services/slideshow_selection.py`, `src/media_hygiene/review/templates/pick_acting.html.j2`

## Problem

Follows 0655 (PARTIAL, commit 7de56049): 📺 *On the TV* is in the pick bar of search, browse and
the burst review, the pages that already serve the albums API (`action: "tv"` resolves the page's
keys to index files, never a path from the request). The phone page (`mh import --phone` /
freeing a phone, on the PC) and `/person` have no albums API, so neither ➕ nor 📺.

Decided in the review of 2026-11-08: give these two pages the albums API (same bar, same features
everywhere), rather than a `tv` endpoint of their own. The junk, quarantine and import reviews
stay without 📺 (decided the same day: nothing to show on a TV there).

## Fix

1. Serve the albums routes on the phone page's and `/person`'s servers (shared module, as
   search/browse), with their own key→index-file picker; carry the TV slot to their server.
2. The shared `pick_*` bar shows 📚 *Album* ▾ and ▶ *Slideshow* ▾ (0660) there (skill `photo-picking-pages`).
3. Off the PC (a paired phone) the pages stay read-only: ➕ hidden there, the slideshow menu hidden too
   (0660: the phone keeps its own *Show on the TV* buttons).

## Acceptance

- [ ] ➕ and 📺 in the bar of the phone page and `/person` (tests), picked or the page's files
- [ ] Keys resolved from the index only (a test with a forged path refused)
- [ ] Docs en/fr; `docs_screenshots` flagged stale
