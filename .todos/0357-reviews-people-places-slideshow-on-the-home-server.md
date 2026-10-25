# 0357 — The reviews, `review-sort`, `people`, `places` and `slideshow` on the home server

- **Priority**: Medium
- **Batch**: home
- **Depends**: 0356
- **Files**: `src/media_hygiene/review/`, `src/media_hygiene/services/review_serving.py`, `src/media_hygiene/services/reviewing.py`, `src/media_hygiene/services/people_page.py`, `src/media_hygiene/people/app.py`, `src/media_hygiene/places/`, `src/media_hygiene/slideshow/app.py`, `src/media_hygiene/review/apply_api.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `documentation/en/commands/`, `documentation/fr/commands/`

## Context

Phase 2b of the single server (maintainer, 2026-10-24), after search and browse (0356) proved the
prefixes, the shared routes and the session-long state. These pages never change a photo
(`READ_ONLY_COMMANDS`, `cli/safety.py`); they write only the tool folders: `decisions.json`,
`sort-decisions.json` (`/reports`), `config.toml` and `/config/people/*.toml` (places, people), the
previews (`/cache`). `shrink` changes photos: it waits for 0361.

## What to do

1. Each page's app under its prefix, as 0356 did (the reviews: one prefix per kind and report;
   `review --report X` becomes a URL parameter; review-sort: the classify plan).
2. *Apply now* (0243): the page asks for the step `clean --decisions` through the channel of 0355
   (the server stays up, the page shows the step running, then its new state).
3. A page whose saves change the settings (people, places) and the other pages reading them in
   the same session: they rely on 0358 (settings read again when their files change); until it
   lands, those two pages keep their own container (say it in the catalog).
4. `slideshow --lan` and the phone pages: through the pairing of 0360; until it lands, the LAN
   pages keep their own container.
5. Heavy work stays out of the server: `people`'s face analysis and `tags` run as steps (their own
   container), the page reads their results (index changes seen by 0358).
6. Memory: measure the server's resident memory after each page opened once, then after search by
   meaning (CLIP's text model); free what no page used for some minutes (a named constant; say in
   the report whether it should be a setting).
7. Tests per page through the home server; the docs of each page en + fr; `docs_screenshots` to
   run (said, not run).

## Acceptance

- Every read-only page opens from the home page in under 1 s (measured), its command typed alone
  works as before.

## Gain

Each review, people, places and slideshow page: from about 5.5 s (*estimated* after 0354) to under
1 s (*estimated*).
