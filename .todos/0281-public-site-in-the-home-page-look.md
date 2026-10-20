# 0281 — The public documentation site in the home page's look

- **Priority**: Low — decided by the maintainer on 2026-10-20 (0270, decision 1): a separate, smaller TODO
- **Batch**: docs
- **Depends**: 0270
- **Files**: `.config/mkdocs/mkdocs.yml`, `.config/mkdocs/overrides/stylesheets/guide.css`, `.config/mkdocs/overrides/` (new: `stylesheets/theme.css`, `main.html`), `documentation/en/development.md`, `documentation/fr/development.md`

## Context

Since 0270, the documentation the tool serves (`/docs/<locale>/<page>/`) wears the home page's
look: its tokens (`review/templates/theme.css.j2`), its fonts, the meerkat. The public site
(MkDocs Material on GitHub Pages) still wears Material's indigo default, with its own
`guide.css` for the "in short" guides. A reader going from the README to the site, then into
the tool, sees two looks.

## What to do

1. Give the site the same palette: map Material's variables (`--md-primary-fg-color`,
   `--md-accent-fg-color`, `--md-default-bg-color`, `--md-code-bg-color`, the `slate` scheme)
   to the tool's tokens (`--mk-*`, `--mh-*`), light and dark, in one stylesheet of
   `overrides/`. Keep a single source of the values if possible (to check: generate the site's
   stylesheet from `theme.css.j2` at `docs_build`, or copy the values with a test comparing them).
2. The fonts: the tool ships its own (`media_hygiene/assets/`); the site may load them from the
   same files (copied into `overrides/`), never from a CDN.
3. The meerkat: the avatar as the site's logo and favicon (`theme.logo`, `theme.favicon`).
4. `guide.css`: its colours from the same tokens (the in-image port lives in
   `src/media_hygiene/docs/templates/doc.css.j2`).

## Acceptance

- `docs_build` (strict) still passes; `tests/unit/test_docs_site.py` unchanged.
- Light and dark checked by eye on two pages (a guide, a command page): to do by the maintainer
  or with `docs_serve`.

## Explicit NON-goals

- No change to the pages themselves, nor to the docs served by the tool.
