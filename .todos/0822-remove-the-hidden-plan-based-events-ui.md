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
