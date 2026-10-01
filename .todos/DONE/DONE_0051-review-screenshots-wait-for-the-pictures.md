# 0051 — Docs: the burst review screenshots are taken before the pictures show

- **Priority**: Low — documentation only; the page itself works
- **Batch**: docs
- **Depends**: —
- **Files**: `tests/support/docs/browser.py`, `documentation/en/images/review.webp`, `documentation/fr/images/review.webp`, `documentation/en/images/review-aside.webp`, `documentation/fr/images/review-aside.webp`

## Context

Seen while running `docs_screenshots` for TODO 0049 (2026-09-30). In `review.webp` (en and fr) every
card of the second series shows a broken-image icon over its label ("…pt", "…nservée") instead of
the picture; the previous French capture had its first two cards still blank (being loaded).
`tests/support/docs/browser.py::review` presses `ArrowRight`, waits a fixed `PAUSE_MS`, then takes
the screenshot: nothing waits for the `<img>` of the new series to be loaded and decoded, so the
result depends on the machine's speed. (Not checked: that the pictures do show in a real browser
given time; if they never do, this becomes a bug of the review page, not of the capture.)

## Proposal

- Before each review screenshot, wait until every `#shots img` is `complete` with a
  `naturalWidth > 0` (Playwright `page.wait_for_function`), after the series change; keep the pause
  for the transitions only.
- Refresh the captures (`docs_screenshots`, en + fr) and look at the four review pictures.

## Explicit NON-goals

- No change to the review page itself, unless the check above shows the pictures never load.

## Acceptance

- [ ] `review.webp` and `review-aside.webp` (en + fr) show the five pictures of the series.
