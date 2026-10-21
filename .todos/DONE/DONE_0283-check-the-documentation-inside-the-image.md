# 0283 — Check the documentation inside the image: image layers and the pages in a browser

- **Priority**: Medium
- **Batch**: docs
- **Depends**: —
- **Files**: `Dockerfile`, `src/media_hygiene/docs/templates/doc.html.j2`, `src/media_hygiene/review/docs_app.py`
- **Needs maintainer**: `build`, `dive_ci`, then `hygiene home` and a Doc link opened in a browser (light, dark, narrow window)

## Context

Remainder of 0270 (PARTIAL, commit `482d7eb`, merged with PR #32): the `docs` stage renders
`documentation/` into the image and every page server answers `/docs/<lang>/<page>/`. CI's image
job built the image and its e2e test checks the docs are inside without their renderer (passed
on PR #32). Not checked: `dive_ci` on the new layer (+6.9 MB uncompressed, **measured** with
`du -sk` in the stage) and the look of a doc page.

## What to check

1. `build`, then `dive_ci`: the gate passes; the docs layer holds HTML/CSS/images only.
2. `hygiene home`, click a "Doc" link of the home page and of a review page's bar, then the
   Ctrl+K palette's Documentation group: the chapter opens in the tool's look, menu, table of
   contents, previous/next, FR/EN switch.
3. Light and dark theme, a narrow window (phone width).

Anything wrong: fix it here, with a test; nothing wrong: close DONE.

## Closed (2026-10-21)

1. **Image layers.** `dive_ci` had stopped checking anything: dive 0.13.1 reading `docker://`
   from Docker 29.8 extracted nothing and exited 0 in 1.6 s (*measured*), so the gate passed
   blind. `dive` and `dive_ci` now read the saved archive (`_dive_archive` in
   `.devcontainer/scripts/helpers/docker.sh`: `docker save` into a temporary volume, then
   `docker-archive://`). Result (*measured*): efficiency 99.1 % (gate 98 %), user waste 1.59 %
   (gate 3 %); an impossible threshold (99.9 %) fails with code 1. The docs layer is 6.6 MB:
   128 `.html`, 46 `.webp`, 2 `index.json`, nothing else.
2. **Pages in a browser.** Checked by the maintainer with `hygiene home`: the chapters open in
   the tool's look, menu, table of contents, previous/next, FR/EN, both themes, narrow window.
   One defect: "Back to the tool" led the docs' new tab to `/`, a second tab of the tool. It now
   closes the docs tab, so the browser shows the tab left (`doc.js.j2`); where a browser refuses,
   the link still leads to `/`. Chromium and Firefox let a tab opened by a link close itself,
   page turns included (*measured* with Playwright 1.57 in `media-hygiene-docs-browser:1.57.0`);
   confirmed by the maintainer in their browser.
