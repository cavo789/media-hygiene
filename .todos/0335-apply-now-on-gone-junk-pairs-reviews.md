# 0335 — *Apply now* on the `--junk` and `--pairs` reviews

- **Priority**: Medium
- **Batch**: review-ui
- **Depends**: —
- **Files**: `src/media_hygiene/services/pairs_reviewing.py`, `src/media_hygiene/services/unwanted_reviewing.py`, `src/media_hygiene/cli/review_modes.py`, `src/media_hygiene/review/templates/unwanted_review.html.j2`, `src/media_hygiene/review/templates/pairs_review.html.j2`, `src/media_hygiene/review/templates/{unwanted,pairs}_review.js.j2`, `tests/integration/test_review_apply.py`, `documentation/en/commands/review.md`, `documentation/fr/commands/review.md`

## Why

Left over from 0333 (one page frame): the bursts and `--near` reviews show *Apply now* in their
bar when the home page opened them (0288); `--gone`, `--junk` and `--pairs`, now on the same
frame, do not. Same page, same place, same features (memory *Same features on every page*).

## What

- `serve_pairs_review`, `serve_unwanted_review` take a `ReviewStart` (as
  `serve_near_review`) and an `ApplyOffer` whose `pending` is "something decided in this
  session"; the CLI passes `page_apply(runtime)` and ends on `end_on_applied`.
- The bar includes `apply_now.html.j2`; each page's script calls `window.mhApplyNow(decided > 0)`
  after each save, as `near_review.js.j2` does.
- Not on `--gone` (decided 2026-10-25, review of the feedback of 2026-10-23): its answers move
  no file, a button there would do nothing the user can see.

## Overlaps

0320 (the `--junk` review on the shared picking grid) adds *Apply now* to `--junk`: whichever
runs first does it there, the other skips that page.

## Tests

`test_review_apply.py`: each of the two pages, opened from home, shows the button once
something is decided and ends with the step's code.

## Docs

`review.md` (both languages): *Apply now* on every review page that moves files (not `--gone`: said why).
