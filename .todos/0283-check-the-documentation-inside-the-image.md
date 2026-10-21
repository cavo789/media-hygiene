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
