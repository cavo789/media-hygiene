# 0161 — `undo`: put several files back at a time, like `clean`

- **Priority**: High — on Windows, undoing a clean takes 2.9× as long as the clean itself (measured); a user who undoes 90,000 copies waits hours
- **Batch**: journal
- **Depends**: —
- **Files**: `src/media_hygiene/actions/undo.py`, `src/media_hygiene/actions/parallel.py`, `src/media_hygiene/actions/restore.py`, `src/media_hygiene/actions/outcome.py`, `tests/integration/test_clean_undo.py`, `tests/integration/test_undo_interrupted.py`, `tests/integration/test_undo_sort.py`

## Context

Measured on 2026-10-14 by the maintainer with `tests/measure/mh-measure.ps1` (Windows, Docker
Desktop, test folder under `%TEMP%`, quarantine on another mount):

| Copies | `clean` (4 at a time, 0149) | `undo` of that clean | ratio |
|---|---|---|---|
| 2,001 (1.3 GB) | 20 s | 56 s | 2.8× |
| 6,001 (6.3 GB) | 1 min 21 s | 3 min 53 s | 2.9× |

`UndoExecutor.run` (`actions/undo.py`) restores one action after the other
(`for entry, reversal in reversed(todo)`), while `clean` hands its actions to
`actions/parallel.run_all` (4 worker threads, `WORKERS`). Each restore through Docker Desktop's
file sharing is dominated by I/O latency (copy back from the quarantine, compare), the same cost
`clean` overlaps.

## What to do

1. Run the reversible actions through `run_all` (same `WORKERS`), each file keeping its own
   sequence: journal `pending`, `perform`, journal `done`.
2. Keep in series, after the files, what depends on order: folder actions (`FOLDER_ACTIONS`,
   a `sort` undo removes the folders it created, deepest first), orphan sidecars, and
   `remove_emptied_folders` (two threads emptying the same quarantine folder must not race:
   run it once at the end over the folders touched, or under a lock).
3. Thread safety: `Tally` counters and lists under a lock (as `JournaledChanges` in 0149);
   the screen updated from the calling thread only (`shown_on`).
4. Ctrl+C / `docker stop`: files not started are cancelled, the ones under way end; a second
   `undo` resumes (the `pending` entries of the undo phase are judged as today).
5. Do not reorder what must stay reversed: two actions on the same path (a file moved by
   `sort`, then its name taken by another) stay in their reversed order. Check whether such
   chains exist in a `sort` journal before parallelising sort undos; if they do, run a chain
   in one worker.

## Acceptance

- `undo` of a clean of 6,001 copies on the maintainer's Windows test folder takes about as long
  as the clean (*estimate*: 3 min 53 s → about 1 min 20 s, −65 %, from the clean's measured
  time with the same workers); measured with `mh-measure.ps1` steps 5a/5b.
- Tests: at most `WORKERS` restores at once; an interrupted parallel undo resumed by a second
  `undo`; a `sort` undo still removes its folders after their files; the existing undo tests
  pass unchanged.
- Say in the report whether the worker count should become a `config.toml` setting (shared
  with `clean`'s, see 0149).
