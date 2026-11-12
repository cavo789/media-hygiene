# 0721 — `history` lists a run known only from its quarantine copy

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_history.py`, `src/media_hygiene/actions/runs.py`, `src/media_hygiene/actions/journal_copy.py`, `src/media_hygiene/paths/quarantines.py`, `tests/unit/test_history_here.py`

Follows DONE 0697 (`.todos/DONE/DONE_0697-run-journal-copied-beside-its-quarantine.md`, commit 673c07f9): each run's journal is copied as `<run>.jsonl` beside its quarantine folder, and `undo` can rebuild from it. `history` still lists only the runs of `/journal`, so a run whose journal is missing is invisible until an `undo` takes it back.

Decided by the maintainer in the review of 2026-11-12.

## What

- `history` also lists a run found only as a quarantine `<run>.jsonl` copy (journal missing), marked **from the quarantine**, before any undo takes it back.
- Reads every quarantine (the one-letter drive folders included), as the other readers do.
- Such a run is shown with the undo line that works for it.

## Acceptance

- [ ] Test: journal deleted, copy kept: the run is listed and marked; with both present it is listed once, unmarked.
- [ ] A quarantine not mounted: no traceback, the run is not invented.
- [ ] French strings; `commands/history.md` EN + FR.
