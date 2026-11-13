# 0754 — What 0572 left: Search › Events: trust what the disk holds, not a classify plan the user forgot

- **Priority**: Medium
- **Batch**: backlog
- **Depends**: —
- **Files**: `.todos/DONE/0572-search-events-tab-without-a-classify-plan.md`

Split from section 0572 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0572-search-events-tab-without-a-classify-plan.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- Remove the plan-based UI now hidden (`events_choice`/`events_sure`/`events_rule`/
- Grid never stale under an event (test)
- Moved rows found by content; sorted-by-any-means counted (tests per move kind)
- Plan age shown, or the tab works without a plan (per the maintainer's choice)

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-13)

### Done
- Plan age / without a plan: the maintainer chose the tab without a plan (0572); it is built
  from the index (`search/span_events.py`) — done by 0572.
- Grid never stale under an event, moves of every kind (`sort` or the Explorer into a dated
  folder: leaves; `undo` back out: returns), with the page left open: each ask reads the index
  again (test `test_the_grid_follows_moves_while_the_page_stays_open`,
  `tests/integration/test_span_events.py`). "Sorted by any means" is the path condition of
  `/search` (`Sorting.LEFT`), so every kind of move counts once the index records it.

### Not done
- Remove the plan-based UI hidden behind `SPAN = true` (`events_choice`/`events_sure`/
  `events_rule`/`events_progress` templates, `EventsDesk.opener/state/event`, the sort routes
  of `events_choose`, their tests), and rewrite what `sort/11` (en + fr) still says of it.
  **Reason:** about 1,600 lines of JavaScript shared with review-sort's choices and no browser
  test in the devcontainer: a removal to do with CI's headless Chromium checking each step.
