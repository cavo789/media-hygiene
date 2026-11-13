# 0765 — What 0666 left: Every page keeps its view in the URL: Back, reload and a bookmark work

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: —
- **Files**: `.todos/DONE/0666-page-view-kept-in-the-url.md`, `src/media_hygiene/review/templates/page_frame.html.j2`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/review/templates/pick_viewer.js.j2`, `src/media_hygiene/review/templates/review_board.js.j2`, `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/places/templates/places.html.j2`

Split from section 0666 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0666-page-view-kept-in-the-url.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- View keys of junk, gone, intruders, people, places, quarantine, shrink (their tab/filter):
- Other templates still read `URLSearchParams(location.search)` directly (person, quarantine,
- The helper is in the shared templates only

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-13)

### Done
- *The helper is in the shared templates only*: every template reads the query string through
  `window.mhView.get` (person, quarantine, quarantine purge, album edit, album bar, disk space,
  events' late list); `view_state.html.j2` gains a `"path"` kind (≤ 4096 characters) for
  `/person?path=`. Tested: no `location.search` outside the helper
  (`tests/unit/test_view_state.py`), the TV screen excepted (ES5, no frame, its own `here=1`).
- View keys: gone (deleted files), unwanted (junk) and shrink keep the group / video shown in
  `g`, read back on load (as bursts, near, pairs). People already kept `who` (0667). Docs EN + FR
  (`commands/library.md`).

### Not done
- Intruders (the ticks of its two tables) and places (the list's typed filter, the tab shown):
  their filter state is several values per table, not one key; each needs its own choice of keys.
  **Reason:** out of this lot's size; code work, no maintainer needed.
- Quarantine: `?run=` is read; *Every run* is a link, so the URL already says the view. Nothing left.
