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

- [ ] Written at the end of each writing run, atomically, read back
- [ ] Readers of the quarantine (pages, purge, `undo --from-quarantine`) ignore it as a file and
      `undo` uses it when `/journal` lacks the run (test: journal wiped → undo works)
- [ ] `purge <run>` removes it with the run; a drive quarantine (`/quarantine/<x>`) handled
- [ ] Docs EN + FR (`reference-safety.md`)
