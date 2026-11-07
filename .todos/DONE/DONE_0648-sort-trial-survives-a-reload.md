# 0648 — Sort trial on the page: Undo and Sort the rest survive a reload

- **Priority**: Low
- **Batch**: sort
- **Depends**: —
- **Files**: `src/media_hygiene/services/sort_trial.py`, `src/media_hygiene/actions/`

## Problem

Follows 0640 (commit 06b35478). *Undo* and *Sort the rest* last as long as the page; after a reload
only `mh sort` and History remain.

## Decided (2026-11-07, maintainer, review of the iterate of 2026-11-06 (3))

They survive a reload, from a marker in the journal: the run is a trial.

## Acceptance

- [ ] Trial, reload: the photos, *Undo* and *Sort the rest* are back, read from the journal
- [ ] Undone or finished trial: nothing offered; an older journal without the marker still loads
