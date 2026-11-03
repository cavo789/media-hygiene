# 0522 — Home page: one "Apply all" for the choices pending on every page

- **Priority**: Medium
- **Batch**: home
- **Depends**: 0511
- **Files**: `src/media_hygiene/review/home_parts.py`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/review/apply_api.py`, `src/media_hygiene/review/apply_relay.py`, `src/media_hygiene/services/home.py`, `src/media_hygiene/review/templates/`

## Asked (maintainer, 2026-10-30)

Each page has its *Apply now* (0511); applying everything means opening each page.

## What

- The home page counts what waits in every decisions file (bursts, near, pairs, intruders,
  unwanted, search set aside): "37 choices pending on 3 pages", each page named with its count
  and a link to it.
- One *Apply all* button: one `clean --decisions` run (one journal run, so one `mh undo`), the
  same `ApplyOffer` / `apply_now` template, at the same place in the bar.
- The count is read back from disk after applying (save proven rule), and goes to zero.
- With 0521, no confirmation: an Undo toast.

## Done when

With choices pending on two pages, one click applies both, the count reads 0 from disk, and one
`mh undo` takes both back (test).

## Outcome (2026-11-03) — DONE

- All the pages write one `decisions.json` (keys `bursts`, `near`, `pairs`, `unwanted`, `gone`,
  `chosen`), and the home page's `apply` step (`clean --tier near --decisions`) already applies
  them in one journal run: no new route, no second runner.
- `cli/home_pending.py`: counts per page what waits (a series' discarded shots, near groups and
  pairs not left planned, unwanted set aside, gone deleted, search chosen), read from disk at each
  state (`HomeState.pending`, `HomePending`/`PendingPage`); a broken file shows no count.
- `pendingBanner` (`home_inline.js.j2`): "Choices waiting to be applied: N", each page linked with
  its count, **Apply all** = the `apply` step.
- Test `tests/integration/test_apply_all.py`: junk review + search choices, one run, count 0 from
  disk, one `undo` restores both; `tests/unit/test_home_pending.py`.
- Deviation: a banner at the top of the home page (like the update banner), not the bar's
  `apply_now` template: the home page has no review bar. Intruders and `people` set aside live in
  other files and are not counted (follow-up if wanted).
- `docs_screenshots` should run.
