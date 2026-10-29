# 0493 — Search and browse in the home page's frame

- **Priority**: High
- **Batch**: page-shell
- **Depends**: 0491
- **Files**: `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/services/search_app.py`, `src/media_hygiene/review/templates/page_frame.html.j2`

## Why

The maintainer, 2026-10-29, opening *Albums* from the home page: "Le layout n'a plus rien à
voir avec le gabarit de mh, on a l'impression d'avoir quitté le programme." Every page but the
home page wears the thin violet bar of 0268 (`page_header.html.j2`); the home page alone has the
indigo sidebar, the top bar and the meerkat. Decision (option 1 of three offered): **every page in
the home page's frame**, page by page, Albums first. Memory: every page the same layout, the same
features at the same place.

## What

`search` and `browse` (tile pages: load the skill `photo-picking-pages` first) in the shell, the
*Find* stage highlighted; their fixed bar (0463) stays at the top of the main area; the grid keeps
the same features (picking, keys panel, large view). Both served by `mh search`/`mh browse` alone
and from the home server.
