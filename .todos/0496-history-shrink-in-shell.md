# 0496 — History and shrink in the home page's frame

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: 0491
- **Files**: `src/media_hygiene/review/templates/history.html.j2`, `src/media_hygiene/review/templates/shrink.html.j2`, `src/media_hygiene/services/history_here.py`, `src/media_hygiene/services/shrink_page.py`

## Why

The maintainer, 2026-10-29, opening *Albums* from the home page: "Le layout n'a plus rien à
voir avec le gabarit de mh, on a l'impression d'avoir quitté le programme." Every page but the
home page wears the thin violet bar of 0268 (`page_header.html.j2`); the home page alone has the
indigo sidebar, the top bar and the meerkat. Decision (option 1 of three offered): **every page in
the home page's frame**, page by page, Albums first. Memory: every page the same layout, the same
features at the same place.

## What

History (tools: *History and undo* highlighted) and shrink in the shell.
