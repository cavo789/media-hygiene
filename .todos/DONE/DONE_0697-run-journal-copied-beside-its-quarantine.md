# 0697 — Each run's journal copied as `<run>.jsonl` beside its quarantine folder

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/actions/quarantine.py`, `src/media_hygiene/actions/journal.py`, `src/media_hygiene/services/undo.py`, `src/media_hygiene/paths/quarantines.py`

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0687 (commit f3ffdef4, PARTIAL) left point 2 undone: a copy of the run's journal travelling with
its quarantine. Decided: a file `<quarantine>/<run>.jsonl` **beside** the run's folder, never
inside it (every reader of a run folder would take it for a set-aside file).

## Acceptance

- [x] Written at the end of each writing run, atomically, read back
- [x] Readers of the quarantine (pages, purge, `undo --from-quarantine`) ignore it as a file and
      `undo` uses it when `/journal` lacks the run (test: journal wiped → undo works)
- [x] `purge <run>` removes it with the run; a drive quarantine (`/quarantine/<x>`) handled
- [x] Docs EN + FR (`reference-safety.md`)

## Result (2026-11-12)

`actions/journal_copy.py` (write: a `.tmp` draft, fsync, rename, read back byte for byte) and
`services/journal_beside.py`. Written at the end of `clean`, `sort` and every `new_run` run
(album, xmp, shrink, repair, import…, in a `finally`: an interrupted run too), and after each
undo (refreshed; erased once the run's folder is gone). Beside the run's folder in each
quarantine that holds one (`/quarantine`, `/quarantine/<x>`). `undo` first takes back into
`/journal` the copies of the runs it lacks, never over a journal. `purge_run` erases it.
Readers list runs as folders and walk run folders only: the copy is never a run nor a file
set aside. Tests: `tests/integration/test_journal_copy.py` (6: beside + readers, journal
wiped → undo restores every byte, never over a journal, partial undo refreshes, purge,
D:'s quarantine).
