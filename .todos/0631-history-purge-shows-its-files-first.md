# 0631 — History: the same Purge as Disk space, its files shown first

- **Priority**: Medium
- **Batch**: one-interface
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/`, `documentation/en/commands/history.md`, `documentation/fr/commands/history.md`

## Problem

Follows 0616 (commit a4f89f3d). Disk space opens a run's tiles, states count and size on the
button and runs `purge <run> --yes` after one confirmation, the result read back from disk. The
`purge` of the History page still asks in the window of `mh`: two ways to do one thing, and one
that shows nothing first (rule *Seeing first*).

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06)

Same route as Disk space.

## Acceptance

- [ ] History's Purge opens the run's tiles and uses the route of Disk space; no question in the window
- [ ] A missing or wrong count is refused, nothing written
- [ ] Both languages of the docs updated; `docs_screenshots` flagged as stale
