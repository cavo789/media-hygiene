# 0760 — What 0655 left: 📺 *On the TV* on the review pages, `/person` and the phone page; "replaced" told on the remote

- **Priority**: Medium
- **Batch**: tv-slideshow
- **Depends**: —
- **Files**: `.todos/DONE/0655-tv-button-on-every-tile-page-replaced-on-remote.md`, `src/media_hygiene/review/templates/pick_acting.html.j2`, `src/media_hygiene/services/slideshow_selection.py`

Split from section 0655 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0655-tv-button-on-every-tile-page-replaced-on-remote.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- 📺 on the other review pages with tiles (`unwanted_review`, `quarantine`, `import_pick`), on
- 📺 in the bar of each review page, `/person` and the phone page when a TV is paired (tests)
- Picked files, or nothing picked → the page's files, as on search
- The remote tells "replaced" after a selection replaced a running show (test)

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-13)

### Done
- Checked in the code, nothing to write (already done by 0655/0660/0694, only unticked):
  ▶ *Slideshow* ▾ with 📺 *On the TV* in the bar of the burst review (`_TV_PAGES` in
  `services/review_file.py`), `/person` (`person/door.py`, `tv_here`) and the phone page served
  by the home server (`services/phone_review.py`, `phone_here_parts.py`), hidden until
  `/api/tv-paired` says yes; picked files or, nothing picked, the page's files
  (`pick_grid.js.j2`, `toTv`). Tests: `tests/unit/test_tv_selection.py`,
  `test_keyed_albums.py`, `test_phone_here.py` (37 passed, 2026-11-13).
- "Replaced" told on the remote: `Desk.replaced` (`slideshow/desk.py`), the `#replaced` line of
  `slideshow.html.j2`/`slideshow.js.j2`; test
  `test_the_remote_says_once_a_selection_replaced_a_show`.

### Not done
- 📺 on `unwanted_review`, `quarantine`, `import_pick`.
  **Reason:** none of the three has an albums API, and the TV resolves keys from the index
  only. Quarantined files and import candidates are not in the index (moved out / still on
  the source), so a show of them needs a new, non-index source: a design decision for the
  maintainer (is a slideshow of set-aside or not-yet-imported files wanted at all?). For
  `unwanted_review` it is feasible: wrap `UnwantedApp` in `WithAlbums(…, keyed_albums(runtime,
  rank → photo path, tv), …)` from `review_here.on_tv` and add the template to `_TV_PAGES`;
  `review/unwanted_session.py` is at 200/200 lines, so the rank → path lookup goes in a new
  module. Left with the question of whether a show of likely-junk photos is worth a button.
