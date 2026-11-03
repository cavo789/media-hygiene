# 0498 — The HTML reports in the home page's look

- **Priority**: Low
- **Batch**: page-shell
- **Depends**: 0491
- **Files**: `src/media_hygiene/report/templates/base.html.j2`

## Why

The maintainer, 2026-10-29, opening *Albums* from the home page: "Le layout n'a plus rien à
voir avec le gabarit de mh, on a l'impression d'avoir quitté le programme." Every page but the
home page wears the thin violet bar of 0268 (`page_header.html.j2`); the home page alone has the
indigo sidebar, the top bar and the meerkat. Decision (option 1 of three offered): **every page in
the home page's frame**, page by page, Albums first. Memory: every page the same layout, the same
features at the same place.

## What

`report/templates/base.html.j2` copies the thin bar. A report has no server: offer the shell's
look (colours, meerkat, top bar) with a sidebar of the report's own pages only, and ask.

## Decided (2026-11-03)

By the maintainer: the priority is to **stay inside the web page** (the server). When the reports list is opened from mh's page, a report opens inside the home page's frame (served by the server, the shell's sidebar and bar), not as an external .html file. The static .html files, opened without a server, get the shell's look (colours, meerkat, top bar) with a sidebar of the report's own pages only, as a fallback.
