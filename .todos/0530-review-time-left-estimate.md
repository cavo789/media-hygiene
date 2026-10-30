# 0530 — Review pages: time left at the user's own pace

- **Priority**: Medium
- **Batch**: review
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/`, `src/media_hygiene/review/templates/pick_grid.js.j2`

## Asked (maintainer, 2026-10-30)

UX brainstorm: say how long is left, to decide whether to go on now.

## What

- In the bar of each review page: "1,240 series left, about 4 min at your pace".
- Pace measured in this session only (cases decided / time spent, idle gaps over 60 s left
  out); before 10 cases, the count only, no time.
- Pure page code, nothing stored.

## Done when

The estimate appears after 10 decisions, ignores idle gaps (test of the pace function).
