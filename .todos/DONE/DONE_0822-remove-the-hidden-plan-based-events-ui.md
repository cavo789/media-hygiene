# 0822 — Remove the plan-based Events UI hidden behind `SPAN = true`

- **Priority**: Low
- **Batch**: cleanup
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/events_choice*`, `src/media_hygiene/review/templates/events_sure*`, `src/media_hygiene/review/templates/events_rule*`, `src/media_hygiene/review/templates/events_progress*`, `src/media_hygiene/review/events_*.py`, `documentation/en/sort/11*.md`, `documentation/fr/sort/11*.md`

Decided by the maintainer in the inbox of 2026-11-14 (follows `.todos/PARTIAL/PARTIAL_0754-*.md`).

## Context

Since 0754 the Events tab no longer shows the plan-based choice; its code stays, hidden
behind `SPAN = true`: about 1,600 lines of JavaScript (`events_choice`/`events_sure`/
`events_rule`/`events_progress` templates), `EventsDesk.opener/state/event`, the sort
routes of `events_choose`, and their tests. Part of it is shared with review-sort's choices.

## Proposal

Remove it step by step, each step checked by CI's headless Chromium walk of the Events tab
and of review-sort (no browser test in the devcontainer); keep what review-sort still uses.
Rewrite what `sort/11` (EN + FR) still says of the old way.

## Acceptance

- [ ] `SPAN` and the hidden templates, routes and tests gone; review-sort unchanged (its tests)
- [ ] CI's browser walks green; `docs_screenshots` said if a capture changes
- [ ] Docs EN + FR of `sort/11` match the page

## Status — PARTIAL (2026-11-27)

### Done
- Inventory (unattended run of 2026-11-27): the `Files:` bullet is wrong. The hidden JavaScript
  lives in `src/media_hygiene/search/templates/` (`events_choice.js.j2` 194 lines,
  `events_rule.js.j2` 153, `events_sure.js.j2` 88, `events_progress.js.j2` 27, included by
  `search_events.js.j2` lines 114–117), not in `review/templates/`. The `SPAN` branches are
  in `search_events.js.j2` (lines 11, 121, 133, 222, 248, 261) and `search_events_ahead.js.j2`
  line 15. The plan routes are in `search/events_choose.py`. The `review/events_*.py` modules
  (`events_sure`, `events_rule`, `events_progress`, `events_choices`, `events_rule_choices`,
  `events_rules_view`, `events_rules_order`) are review-sort's and `services/sort_figures.py`'s:
  keep them.
- The span cards (`search_events_span*.js.j2`) share with the plan UI: `eventShown`,
  `eventTile`, `ruleEvent`/`openRuleFor` (`search_rule.js.j2`), `EVENT_KEYS.Backspace`,
  `mayLeave`, the `#eventCard` frame and `P.trial*` (`search_events_trial.js.j2`). Those stay.

### Not done
- The removal itself (templates, `SPAN`, HTML ids of `search_events.html.j2` /
  `search_events_dialogs.html.j2` / `search_sort_setup.html.j2`, texts of
  `search_events_texts.js.j2`, the plan routes of `events_choose.py`, their tests) and the
  rewrite of `sort/11` EN + FR.
  **Reason:** the devcontainer has neither node nor a browser, so not even a JS parse can be
  checked. One stale `byId(...)` left in the IIFE breaks the whole Events tab, and the TODO
  asks for each step to be checked by CI's headless walk. Do it in a session that can run
  the e2e browser walks (`e2e`, or push one step at a time and `ci_watch`), not unattended.

## Status — DONE (2026-11-27)

Remainder completed in three commits (201676ba page, 08bfe65a docs, a132001a routes): see
the feedback of 2026-11-27-2. CI does not run on a branch push without a PR, so each step
was checked by the Chromium walks run locally (`MEDIA_HYGIENE_E2E_BROWSER=1`: trial, pages,
ask dialog: 17 passed) and a jsdom walk of the Events tab (list, card, keys, ← →).
