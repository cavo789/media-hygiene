# 0491 — Every page in the home page's frame: the shared shell

- **Priority**: High
- **Batch**: page-shell
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/home.html.j2`, `src/media_hygiene/review/templates/page_header.html.j2`, `src/media_hygiene/review/page_header.py`, `src/media_hygiene/review/templates/home_base.css.j2`, `src/media_hygiene/review/templates/page_frame.html.j2`, `src/media_hygiene/review/templates/home_link.html.j2`, `tests/unit/test_page_headers.py`

## Why

The maintainer, 2026-10-29, opening *Albums* from the home page: "Le layout n'a plus rien à
voir avec le gabarit de mh, on a l'impression d'avoir quitté le programme." Every page but the
home page wears the thin violet bar of 0268 (`page_header.html.j2`); the home page alone has the
indigo sidebar, the top bar and the meerkat. Decision (option 1 of three offered): **every page in
the home page's frame**, page by page, Albums first. Memory: every page the same layout, the same
features at the same place.

## What

Extract from `home.html.j2` the sidebar (the five stages, the tools, your folders, the version),
the top bar (☰ on a phone, theme switch, documentation FR/EN) and the meerkat into shared
templates (`shell_*.html.j2`, `shell.css.j2`), fed by the same catalog (`cli/menu_catalog_*`),
and make `page_header.html.j2` render that shell instead of the thin bar; the page's own content
goes in the main area, its name in the top bar ("Albums"), the current stage highlighted
(apricot = you are here).

Decisions to write down while doing it:
- A page **served by the home server** (`/albums`, search/browse opened from home): sidebar
  entries are plain links to `/#<space>`.
- A page **served by its own server** (`mh search` typed in the console): a sidebar click must
  end the page as *Back to the home page* does today (`home_link.html.j2`: ends the server,
  waits for home) then open that space — or the entries are shown but only link home. Choose,
  say it in the feedback.
- Tile pages (`page_frame.html.j2`, skill `photo-picking-pages`): the sidebar folds to icons
  (or ☰) so the grid keeps its width; measure the columns lost at 1366 px and 1920 px.
- `test_page_headers.py`: every page served carries the shell (no exemption list by default).

This TODO only builds the shell and moves no page but a test page; each page follows in its own
TODO.
