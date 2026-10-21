# 0282 — Served pages: drop each board's own title, the bar already names the page

- **Priority**: Low
- **Batch**: review-ui
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/templates/pairs_review.html.j2`, `src/media_hygiene/review/templates/near_review.html.j2`, `src/media_hygiene/review/templates/unwanted_review.html.j2`, `src/media_hygiene/review/templates/gone_review.html.j2`, `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/review/templates/phone_review.html.j2`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/people/templates/people.html.j2`, `tests/unit/test_page_headers.py`

## Context

0268/0271/0272 (commit `bae025d`, merged with PR #32) put one bar on top of every served page:
the name, the avatar, the page's name and its doc chapter. Each board kept its own sticky
header below it, whose `<h1>` repeats the page's name. Decided by the maintainer on 2026-10-21
(review of `/todo:iterate` 2026-10-20): drop the repeated title.

## What to do

- Remove the board's `<h1>` (or the part that repeats the bar's page name); keep what the sticky
  header adds: counters, the keys, the progress.
- The page's `<title>` stays (the browser tab).
- Accessibility: one `<h1>` per page remains — the bar's page name becomes it if it is not one yet.
- Leave the HTML reports alone (`report/templates/`): a `file://` report is printed and shared,
  its title is the content (to reconsider separately if wanted).

## Acceptance

- `test_page_headers.py`: each served page has exactly one `<h1>`, and it is the bar's.
- Integration tests of the page servers unchanged otherwise.
- `docs_screenshots` to run afterwards (every capture of these pages changes).
