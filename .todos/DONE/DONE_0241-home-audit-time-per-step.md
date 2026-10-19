# 0241 — Home page audit: the `Time per step` line shown at the end, as in the console

- **Priority**: Low
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/services/home_audit.py`, `src/media_hygiene/cli/home_audit.py`, `src/media_hygiene/console/page_progress.py`, `src/media_hygiene/console/stage_times.py`, `src/media_hygiene/review/templates/home.js.j2`, `tests/integration/test_home_audit.py`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Context

Follows 0211 (PARTIAL): *Audit now* on the home page shows each step's counts, not their
durations; the console audit ends on `Time per step: listing 1.2 s · checks 3.4 s · …`
(`console/stage_times.stages_line`). The stopwatch's stage times are known only at the end.
Decided by the maintainer (inbox, 2026-10-19): show them at the end. Stopping the audit when the
tab is closed (a heartbeat) was dropped.

## What to do

- At the end of a home audit, `GET /api/audit` carries the same line `stages_line` builds
  (same words, same translation, same rounding), shown under the audit's figures.
- Nothing while it runs; nothing after a stopped or failed audit.

## Acceptance

- Integration: the finished home audit's answer holds the line, identical to the console's for
  the same tree; absent after a stop.
- Docs both languages: the home command page.

## Gain (estimated)

Where an audit spends its time, seen in the page as in the console: no need to rerun from `mh`.
