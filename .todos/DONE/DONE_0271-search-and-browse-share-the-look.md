# 0271 — `search` and `browse` wear the home page's look

- **Priority**: Medium — asked by the maintainer (2026-10-20)
- **Batch**: review-ui
- **Depends**: 0268
- **Files**: `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_page_headers.py`, `documentation/en/images/search.webp`, `documentation/fr/images/search.webp`, `documentation/en/images/browse.webp`, `documentation/fr/images/browse.webp`

## Context

0268 writes the theme and header partials and puts the review boards in the home page's look.
`search` and `browse` are served by `search/app.py`, which does not build on
`review/local_app.py` (checked, 2026-10-20). So these two pages need the `/assets/` route
(fonts, avatar) in their own server.

## What to do

- `search/app.py` serves `/assets/` as `local_app.py` does after 0268: only files under
  `media_hygiene/assets/`, the right content types, long cache, the CSP still `self`.
- `search.html.j2` and `browse.html.j2` include the theme and the header:
  - the doc links go to the `search` and `browse` chapters, in both languages;
  - "Back to the home page" appears when the page was opened from it;
  - browse's "Apply now" (0243) keeps its place and its behaviour.
- Layouts, keys and filters do not change.

## Acceptance

- `tests/unit/test_page_headers.py` covers both pages: the header, and the two doc links to their
  chapters.
- `/assets/` refuses a `../`; the existing tests of search and browse pass unchanged.
- The `search.webp` and `browse.webp` captures go stale: say that `docs_screenshots` should run.

## Gain (counted)

Two more pages in the look of the home page, and their help a click away in both languages.
