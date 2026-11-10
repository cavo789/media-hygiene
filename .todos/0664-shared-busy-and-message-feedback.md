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
      shared parts once per page covers them)
- [ ] Headless Chromium with a mocked API answering after 2 s: button disabled, placeholders
      shown, the grid's top unchanged before and after
- [ ] `docs_screenshots` should run

## Where the user gains

Before: 1 page with a loader (measured), several message styles. After: the same on every
page; no double click, no doubt whether a click was taken.
