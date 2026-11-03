# 0495 — People, person and places in the home page's frame

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: 0491
- **Files**: `src/media_hygiene/services/people_page.py`, `src/media_hygiene/person/door.py`, `src/media_hygiene/services/places_build.py`

## Why

The maintainer, 2026-10-29, opening *Albums* from the home page: "Le layout n'a plus rien à
voir avec le gabarit de mh, on a l'impression d'avoir quitté le programme." Every page but the
home page wears the thin violet bar of 0268 (`page_header.html.j2`); the home page alone has the
indigo sidebar, the top bar and the meerkat. Decision (option 1 of three offered): **every page in
the home page's frame**, page by page, Albums first. Memory: every page the same layout, the same
features at the same place.

## What

The people pages and the places map in the shell (*Sort* stage for places, *Find* for people);
the Leaflet map takes the main area's full height; its CSP still allows the shell's assets.
