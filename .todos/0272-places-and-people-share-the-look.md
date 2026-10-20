# 0272 — `places` and `people` wear the home page's look

- **Priority**: Medium — asked by the maintainer (2026-10-20)
- **Batch**: review-ui
- **Depends**: 0268
- **Files**: `src/media_hygiene/places/app.py`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/people/app.py`, `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_page_headers.py`, `documentation/en/images/places.webp`, `documentation/fr/images/places.webp`, `documentation/en/images/people.webp`, `documentation/fr/images/people.webp`

## Context

0268 writes the theme and header partials. `people` is served on `review/local_app.py`, so it
gets `/assets/` from 0268. `places` has its own server, `places/app.py`, and its own policy,
checked on 2026-10-20:

- `PAGE_POLICY` is `default-src 'none'`, scripts and styles from `'self'` and inline, the
  images from `'self'` and the tile server;
- it has no `font-src`, so the embedded fonts would be blocked.

## What to do

- `places/app.py` serves `/assets/` like the other pages, and `PAGE_POLICY` gains
  `font-src 'self'`. The tile server stays the only outside host.
- `places.html.j2` and `people.html.j2` include the theme and the header:
  - the doc links go to the `places` and `people` chapters, in both languages;
  - "Back to the home page" appears when the page was opened from it.
- Leaflet's own stylesheet (`places/static/leaflet.css`) stays. The map's controls and drawer
  take the theme's colours where Leaflet lets a stylesheet set them. The map itself and its
  tiles do not change.

## Acceptance

- `tests/unit/test_page_headers.py` covers both pages: the header, and the two doc links to their
  chapters.
- `places`' policy holds `font-src 'self'` and still names the tile server only; the existing
  tests of both pages pass unchanged.
- The `places.webp` and `people.webp` captures go stale: say that `docs_screenshots` should run.

## Gain (counted)

The last two served pages in the look of the home page. With 0268 and 0271, all eleven pages
look the same (counted from the templates).
