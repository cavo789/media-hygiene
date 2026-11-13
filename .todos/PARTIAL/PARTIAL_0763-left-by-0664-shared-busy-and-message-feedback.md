# 0763 — What 0664 left: One way to say *working*, *done* and *failed* on every page

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: —
- **Files**: `.todos/DONE/0664-shared-busy-and-message-feedback.md`, `src/media_hygiene/review/templates/page_frame.html.j2`, `src/media_hygiene/review/templates/page_frame.css.j2`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/review/templates/home_parts.css.j2`, `src/media_hygiene/review/templates/home_run.js.j2`, `tests/unit/test_page_frame.py`

Split from section 0664 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0664-shared-busy-and-message-feedback.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- Pages with their own fetch helper, not migrated (each needs its own review of its status
- The Undo toast keeps its element (same look, same place, below the stack): merging it into
- Errors' sentence shape (what failed, what stays done, what to do) left to each server answer.
- The three pieces in the frame's templates, no page-specific copy (the test counting

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-13)

### Done
- *The three pieces in the frame's templates, no page-specific copy*: tested over every framed
  page (`tests/unit/test_page_frame.py`,
  `test_every_framed_page_holds_the_busy_and_say_pieces_once`): `#mhSay`, `mhSay`, `mhBusy`,
  `mhPlaceholders` once each.
- The people page's saves go through `mhBusy` (0766).

### Not done
- The other pages with their own fetch helper (places, album*, shrink, disk space, person,
  slideshow, strictness, the review pages, events, quarantine, phone, import, month dialog, the
  album's own `.toast`): each needs its status line reviewed in a browser.
  **Reason:** too wide for one pass without a browser check here; one page per change.
- The Undo toast merged into `mhSay` (a toast with an action, its Z key and 8 s).
  **Reason:** changes the Undo of three reviews; wants the CI browser walk extended first.
- Errors' sentence shape (what failed, what stays done, what to do): per server answer.
  **Reason:** server-side wording over many routes; its own TODO.
