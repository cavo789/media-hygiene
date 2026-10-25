# 0388 — review-sort: see the sure events before accepting them

- **Priority**: Medium
- **Batch**: review-sort
- **Depends**: 0385
- **Files**: `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/review/templates/sort_review_sure.js.j2`, `src/media_hygiene/review/sort_batch.py`, `src/media_hygiene/review/sort_sure.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`

## Why

The maintainer, 2026-10-25: "✔ Accept 85 sure proposals (7403 files): what are we talking
about? How can I see which events?" Nothing lists them; the checkbox *Only the events to decide*
hides them. And the trip of 0385 was one of them while accepting it would have emptied the
user's folders: "sure" must be checkable.

## What

- The confirmation lists the events (name or dates, files that move, destination), each a link
  that opens it on the page; the figures count only the files that move (0385).
- A second filter next to *Only the events to decide*: *Only the sure proposals*, so N/P/→ walk
  them one by one.

## Tests

The list matches `sure_value` over the work list; the filter's walk; both languages.
