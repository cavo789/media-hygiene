# 0268 — The other pages wear the home page's look, and link their own doc chapter

- **Priority**: Medium
- **Batch**: review-ui
- **Depends**: 0266
- **Files**: `src/media_hygiene/review/templates/theme.css.j2` (new), `src/media_hygiene/review/templates/page_header.html.j2` (new), `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/templates/near_review.html.j2`, `src/media_hygiene/review/templates/pairs_review.html.j2`, `src/media_hygiene/review/templates/unwanted_review.html.j2`, `src/media_hygiene/review/templates/gone_review.html.j2`, `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/review/templates/phone_review.html.j2`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_page_headers.py` (new), `documentation/en/images/`, `documentation/fr/images/`

## Context

0266 gives the home page the avonture.be look and the meerkat. The other pages keep their own
look, the GitHub-like tokens of `home.html.j2` today: `review` and its four modes, `review-sort`,
`phone --free`'s page, `search`, `browse`, `places`, `people`. Going from the home page to one
of them would change the visual world.

The maintainer also asked (2026-10-20) that the documentation link at the top point to the
chapter of the page you are on: on `places`, the Places chapter.

## What to do

- **One theme partial** (`theme.css.j2`): the `--mk-*` and `--mh-*` tokens, light and dark
  (following the OS, then the switch of 0266, read from the same `localStorage` key), and the
  fonts of `/assets/`. Each page includes it in place of its own colours. Layout and behaviour
  do not change.
- **One header partial** (`page_header.html.j2`), on every page:
  - "Media Hygiene" and the meerkat avatar, linking back to the home page when it runs;
  - the page's name;
  - "Documentation" in the page's language, plus its English or French twin, both opening the
    page's own chapter (`commands/places/` …, from 0265's catalog `doc`);
  - Quit, where the page has one.
- The reports (`report/templates/`) stay as they are: they are files opened without a server,
  read later; a separate TODO if the maintainer wants them too.

## Acceptance

- `tests/unit/test_page_headers.py`: each page renders its header, and its two doc links point
  to its chapter in both languages (the pages exist: `test_documentation.py`'s helpers).
- The pages' look changes, so every capture under `documentation/{en,fr}/images/` that shows
  one goes stale: say that `docs_screenshots` should run (heavy, by the maintainer).

## Gain (estimated)

Eleven pages (counted from the templates), none in the home page's look today → one look and
one header. From any page, the help for that page is one click away, in both languages.
