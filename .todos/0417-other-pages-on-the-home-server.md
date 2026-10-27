# 0417 — The reviews, people, places and the slideshow served by the home server

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/review/`, `src/media_hygiene/services/review_serving.py`, `src/media_hygiene/services/reviewing.py`, `src/media_hygiene/services/people_page.py`, `src/media_hygiene/people/app.py`, `src/media_hygiene/places/`, `src/media_hygiene/slideshow/app.py`, `src/media_hygiene/review/apply_api.py`, `src/media_hygiene/services/home_audit.py`, `documentation/en/commands/`, `documentation/fr/commands/`

## Why

Leftovers of 0357 and 0358, decided by the maintainer (inbox, 2026-10-27). `search` and `browse`
already open in < 1 s from the home page; the other pages still start a server of their own.

## What

1. Bursts, pairs, junk, gone, people, places, slideshow on the home server (0357 items 1, 3–5): the
   same pattern per page; their views build `/preview/…` from the root: make them relative like
   `near_views`. (`review-sort` goes into the search instead: see the *🗂 Events* TODO.)
2. *Apply now* shows the step running, then the page's new state (0357 item 2).
3. Memory: free idle pages; measure on a real collection (0357 item 6, a step of
   `tests/measure/mh-measure.ps1`).
4. From 0358: the home page's own audit (`page_audit`) re-reads its settings when `config.toml`
   changes; *a file that no longer loads* said on the page, not only in `docker logs`.

## Acceptance

< 1 s from the home page to each page (measure step 35 with `review --near` added).
