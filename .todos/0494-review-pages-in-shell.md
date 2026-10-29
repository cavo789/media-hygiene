# 0494 — The review pages in the home page's frame

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: 0491
- **Files**: `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/templates/near_review.html.j2`, `src/media_hygiene/review/templates/pairs_review.html.j2`, `src/media_hygiene/review/templates/gone_review.html.j2`, `src/media_hygiene/review/templates/intruders_review.html.j2`, `src/media_hygiene/review/templates/unwanted_review.html.j2`, `src/media_hygiene/services/review_file.py`

## Why

The maintainer, 2026-10-29, opening *Albums* from the home page: "Le layout n'a plus rien à
voir avec le gabarit de mh, on a l'impression d'avoir quitté le programme." Every page but the
home page wears the thin violet bar of 0268 (`page_header.html.j2`); the home page alone has the
indigo sidebar, the top bar and the meerkat. Decision (option 1 of three offered): **every page in
the home page's frame**, page by page, Albums first. Memory: every page the same layout, the same
features at the same place.

## What

Bursts, near duplicates, pairs, gone, intruders, unwanted: one template change through
`page_frame.html.j2` once 0491 exists, the *Clean* stage highlighted; keyboard-driven review keys
must not collide with the sidebar's (Ctrl+K palette).
