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
