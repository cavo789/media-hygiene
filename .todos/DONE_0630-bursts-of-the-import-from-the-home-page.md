# 0630 — Import chain from the page: the burst review shows the import's new series only

- **Priority**: Medium
- **Batch**: import
- **Depends**: —
- **Files**: `src/media_hygiene/services/review_here.py`, `src/media_hygiene/review/templates/home_run.js.j2`

## Problem

Follows 0619 (commit 93eb882b). From the home page, the chain's `bursts` step cannot open the
import's own page (the home server holds the port): it says the series wait in the burst review,
and `/review/bursts/` lists the whole library's series, the new ones drowned among them.

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06)

Filter on the last import's new files, as `review --imported` does in the console.

## Acceptance

- [x] Coming from the chain, the page shows only the series of the import's new files, and says so
- [x] A way to see every series stays, one click away
- [x] Set-aside choices still go through `clean --decisions`, *Apply now* offered
- [x] Both languages of the docs updated; `docs_screenshots` flagged as stale
