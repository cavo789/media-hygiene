# 0079 — Docs: screenshots of the `review --near` and `search` pages

- **Priority**: Low
- **Batch**: docs
- **Depends**: —
- **Files**: `tests/support/docs/scenario.py`, `tests/support/docs/screenshots.py`, `tests/support/docs/shots.py`, `documentation/en/clean/11-near-duplicates.md`, `documentation/fr/clean/11-near-duplicates.md`, `documentation/en/reference-tags.md`, `documentation/fr/reference-tags.md`

## Context

TODO 0069 added `review --near` (one near-duplicate group at a time, folder pairs on the left).
The guide `clean/11-near-duplicates.md` describes the page in words only: `docs_screenshots`
shoots the burst review page (`_review` in `scenario.py`, `start_review`/`stop_review` in
`screenshots.py`) but has no step for the near page. A first-time user does not know what to
expect when the browser opens.

TODO 0073 added `search` (a search page over the tags): `reference-tags.md` has no picture of
it either.

## Steps

- [ ] Let `start_review` take the review arguments (`("review",)` or `("review", "--near")`),
  container names kept distinct.
- [ ] In `scenario.py`, a step after the burst review: start `review --near` on the demo, shoot
  the page (`review-near.webp`), stop it and keep its terminal output (`review-near.txt`).
  `scenario.py` is at 199 lines: move a step into its own module first.
- [ ] Demo tree: make sure it has at least one group "to check" and one folder pair with
  several groups, so the page shows its left panel and a 💬 reason line.
- [ ] A `search` step: `tags --no-describe` on the demo (folder, date and place words), then
  `search` served, a query typed (e.g. a folder word of the demo), the grid shot
  (`search.webp`). Same container helpers as the reviews (port 8088).
- [ ] Docs en/fr: the `search.webp` image in `reference-tags.md`, with a hand-written alt text.
- [ ] Docs en/fr: the image (with a hand-written alt text) and the `<!-- capture -->` block in
  the "Decide in the browser" section; `tests/unit/test_documentation.py` green (parity, unused
  screenshots).

## Acceptance

- `docs_screenshots` and `docs_screenshots fr` produce `review-near.webp`, `search.webp` and the
  console block, shown in both languages.
