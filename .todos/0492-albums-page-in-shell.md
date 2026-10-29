# 0492 — Albums page in the home page's frame

- **Priority**: High
- **Batch**: page-shell
- **Depends**: 0491
- **Files**: `src/media_hygiene/share/templates/album.html.j2`, `src/media_hygiene/services/album_pages.py`

## Why

The maintainer, 2026-10-29, opening *Albums* from the home page: "Le layout n'a plus rien à
voir avec le gabarit de mh, on a l'impression d'avoir quitté le programme." Every page but the
home page wears the thin violet bar of 0268 (`page_header.html.j2`); the home page alone has the
indigo sidebar, the top bar and the meerkat. Decision (option 1 of three offered): **every page in
the home page's frame**, page by page, Albums first. Memory: every page the same layout, the same
features at the same place.

## What

First page moved (the one the maintainer saw): `/albums` in the shared shell, the *Share* stage
highlighted; on the phone (paired, read-only) the sidebar keeps only what a phone may open
(0435). Check the album list, an album, the cover and *take out* still work; screenshot both
themes.
