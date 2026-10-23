# 0335 — *Apply now* on the `--gone`, `--junk` and `--pairs` reviews

- **Priority**: Medium
- **Batch**: review-ui
- **Depends**: —
- **Files**: `src/media_hygiene/services/pairs_reviewing.py`, `src/media_hygiene/services/unwanted_reviewing.py`, `src/media_hygiene/services/gone_reviewing.py`, `src/media_hygiene/cli/review_modes.py`, `src/media_hygiene/cli/gone_review_flow.py`, `src/media_hygiene/review/templates/gone_review.html.j2`, `src/media_hygiene/review/templates/unwanted_review.html.j2`, `src/media_hygiene/review/templates/pairs_review.html.j2`, `src/media_hygiene/review/templates/{gone,unwanted,pairs}_review.js.j2`, `tests/integration/test_review_apply.py`, `documentation/en/commands/review.md`, `documentation/fr/commands/review.md`

## Why

Left over from 0333 (one page frame): the bursts and `--near` reviews show *Apply now* in their
bar when the home page opened them (0288); `--gone`, `--junk` and `--pairs`, now on the same
frame, do not. Same page, same place, same features (memory *Same features on every page*).

## What

- `serve_pairs_review`, `serve_unwanted_review`, `serve_gone_review` take a `ReviewStart` (as
  `serve_near_review`) and an `ApplyOffer` whose `pending` is "something decided in this
  session"; the CLI passes `page_apply(runtime)` and ends on `end_on_applied`.
- The bar includes `apply_now.html.j2`; each page's script calls `window.mhApplyNow(decided > 0)`
  after each save, as `near_review.js.j2` does.
- Check first what `status` proposes as the APPLY step after `--gone` answers alone (files
  deleted on purpose, nothing set aside): if no step, the button must not show (`apply_step`
  returns None).

## Overlaps

0320 (the `--junk` review on the shared picking grid) adds *Apply now* to `--junk`: whichever
runs first does it there, the other skips that page.

## Tests

`test_review_apply.py`: each of the three pages, opened from home, shows the button once
something is decided and ends with the step's code.

## Docs

`review.md` (both languages): *Apply now* on every review page.
