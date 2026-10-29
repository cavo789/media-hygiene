# 0497 — Phone page and slideshow: which part of the frame

- **Priority**: Low
- **Batch**: page-shell
- **Depends**: 0491
- **Files**: `src/media_hygiene/review/templates/phone_review.html.j2`, `src/media_hygiene/slideshow/templates/slideshow.html.j2`, `src/media_hygiene/services/phone_review.py`, `src/media_hygiene/services/slideshow_build.py`
- **Needs maintainer**: a decision: the slideshow is full screen on a TV and the phone page is a remote/reader — the shell's ☰ top bar only, or none

## Why

The maintainer, 2026-10-29, opening *Albums* from the home page: "Le layout n'a plus rien à
voir avec le gabarit de mh, on a l'impression d'avoir quitté le programme." Every page but the
home page wears the thin violet bar of 0268 (`page_header.html.j2`); the home page alone has the
indigo sidebar, the top bar and the meerkat. Decision (option 1 of three offered): **every page in
the home page's frame**, page by page, Albums first. Memory: every page the same layout, the same
features at the same place.

## What

The phone page and the slideshow (TV + phone remote) are not desk pages: propose the phone layout
of the shell (top bar + ☰) for the phone page, nothing on the TV, and ask before doing it.
