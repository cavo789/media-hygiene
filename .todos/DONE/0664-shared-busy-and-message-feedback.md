# 0664 — One way to say *working*, *done* and *failed* on every page

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/page_frame.html.j2`, `src/media_hygiene/review/templates/page_frame.css.j2`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/review/templates/home_parts.css.j2`, `src/media_hygiene/review/templates/home_run.js.j2`, `tests/unit/test_page_frame.py`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

*Measured* (2026-11-10, `grep` over `*.css.j2`): a loader / busy style exists in
`home_parts.css.j2` only. Elsewhere each page says things its own way: a status line in the
bar (`say(...)`), a toast (home, `home_run.js.j2`), the Undo toast, a sentence in a dialog.
While a request runs, most buttons stay clickable and nothing moves: on a slow disk the user
clicks twice or thinks the page is stuck (the cause of "is it running?" looks at the console).

## Proposal

Three shared pieces in the frame, used by every page:

- **Busy**: a button that posts is disabled and shows a spinner until the answer; a list or
  grid being loaded shows placeholder tiles of the final size (the grid must not move, as
  the picking contract asks); after 10 s without an answer, one line says what is waited for.
- **Messages**: one `mhSay(text, tone)` — a toast stack at the same place on every page
  (success fades, an error stays until closed, `aria-live`), the bar's status line kept for
  the *saved, read back* sentence only.
- **Errors**: the same sentence shape everywhere (what failed, what stays done, what to do),
  the 500 answer of `serving._answered` already gives it.

## Acceptance

- [ ] The three pieces in the frame's templates, no page-specific copy (the test counting
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
      shared parts once per page covers them)
- [ ] Headless Chromium with a mocked API answering after 2 s: button disabled, placeholders
  → browser check: CI's job (headless Chromium), not the maintainer's (2026-11-12)
      shown, the grid's top unchanged before and after
- [ ] `docs_screenshots` should run
  → captures: one run of `docs_screenshots`, tracked in 0717 (2026-11-12)

## Where the user gains

Before: 1 page with a loader (measured), several message styles. After: the same on every
page; no double click, no doubt whether a click was taken.

## Outcome — PARTIAL (2026-11-11)

### Done

- `review/templates/busy_say.html.j2`, included once by the frame, the home page and the album
  page (like `ask_dialog.html.j2`): `window.mhSay(text, tone)` (one toast stack, bottom centre
  above the Undo toast, `ok`/`info` fade after 6 s, `error` stays until closed, `aria-live`,
  text only), `window.mhBusy(button, work, waiting)` (disabled + spinner until the answer, a
  second click joins the same request, after 10 s one line says what is waited for),
  `window.mhPlaceholders(grid, count)` (placeholder tiles while a grid loads).
- Migrated: the library and every page on `pick_grid.js.j2` (`ask()` posts from a button
  through `mhBusy`; `failed()` and the TV send are error toasts, the bar's line keeps the
  saved sentence); the search's first load shows 12 placeholder tiles and its errors are
  toasts; the home page's posts (`home_run.js.j2` `post`) go through `mhBusy` and its own toast
  style is gone (`toast()` calls `mhSay`).
- Tests: `tests/unit/test_busy_say.py`, `test_pick_pages` counts `#mhSay`; CI browser check
  `tests/e2e/test_ask_dialog_browser.py` + `tests/support/busy_walk.py` (mocked API after 2 s).
- Docs: `commands/home.md` (en + fr), row *While it works*.

### Not done

- Pages with their own fetch helper, not migrated (each needs its own review of its status
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  line): `places.html.j2`, `album.js.j2`/`album_make.js.j2`/`album_root_line.html.j2`/
  `album_edit.js.j2`, `shrink.js.j2`, `disk_space.html.j2`, `people.html.j2`, `person.js.j2`,
  `slideshow*.js.j2`, `strictness.js.j2`, the review pages (`pairs`, `near`, `gone`,
  `intruders`, `unwanted`, `review_choices`), `events_*`/`search_events_grouping`,
  `quarantine.js.j2`, `phone_review.js.j2`, `import_pick.js.j2`, `month_dialog.js.j2`, the
  album's own `.toast` and their local `say()` lines.
- The Undo toast keeps its element (same look, same place, below the stack): merging it into
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  `mhSay` (a toast with an action) is a follow-up.
- Errors' sentence shape (what failed, what stays done, what to do) left to each server answer.
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
- `docs_screenshots` should run (home page and library toasts changed); not run here.
  → captures: one run of `docs_screenshots`, tracked in 0717 (2026-11-12)

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
