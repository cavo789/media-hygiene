# 0744 — What 0521 left: A reversible choice asks nothing: an "Undo" toast replaces window.confirm

- **Priority**: Medium
- **Batch**: page-shell
- **Depends**: —
- **Files**: `.todos/DONE/0521-undo-toast-instead-of-confirm.md`, `src/media_hygiene/review/templates/review_choices.js.j2`, `src/media_hygiene/review/templates/review_obvious.js.j2`, `src/media_hygiene/review/templates/near_review.js.j2`, `src/media_hygiene/search/templates/search_rule.js.j2`, `src/media_hygiene/review/apply_api.py`

Split from section 0521 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0521-undo-toast-instead-of-confirm.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- Moving files to an event (`search_rule.js.j2` goAsk) and *Apply now*: the toast's Undo
- Places (a place given photos, a place deleted) and albums (deleted, a photo taken out):

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-13)

### Done
- Moving files to an event and *Apply now*: already done before this run (checked in the code):
  `search_rule.js.j2` shows `mhUndoToast` with the run's undo after a move (`answer.run_id`),
  `apply_now.html.j2` `offerUndo` runs `mh undo <run>` through `window.mhUndoRun` (0601).
- A place deleted (`places_edit.js.j2`): no question any more when it holds no photo placed by
  hand; the shared Undo toast (now on the places page) saves it again through the page's usual
  save route, read back from `config.toml`. With photos placed by hand it still asks (they go
  back to their GPS, nothing restores them). Test in `tests/unit/test_undo_toast.py`.
- Albums: a photo taken out already offers Undo (0696/0726).

### Not done
- Photos given to a place (`places_map.js.j2`) and albums deleted (`album.js.j2`): still asked.
  **Reason:** each needs its own undo route (take back the hand photos just given; re-create an
  album from its `.history` copy). Filed as 0811.
