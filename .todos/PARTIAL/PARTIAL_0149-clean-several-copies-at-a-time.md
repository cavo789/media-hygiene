# 0149 — `clean`: compare and move several copies at a time

- **Priority**: High — on a Windows folder, a clean of 90,000 copies takes about 3 hours one file at a time (estimate from measured throughputs); four at a time should divide that by up to 4
- **Batch**: journal
- **Depends**: —
- **Files**: `src/media_hygiene/actions/clean.py`, `src/media_hygiene/actions/journaled.py`, `src/media_hygiene/actions/journal.py`, `src/media_hygiene/actions/verify.py`, `src/media_hygiene/services/clean.py`, `tests/unit/test_journal.py`, `tests/integration/`

## Context

Speed and cache review of 2026-10-14 (third pass), for collections of several hundred thousand
files. `CleanExecutor.run` handles one action after the other (`for planned in actions`). For
an exact copy:

1. `checked_removal` reads the kept file and the copy in full (byte comparison, SHA-256 of the
   copy for the journal);
2. the copy goes to `/quarantine`, another bind mount: `rename` fails with `EXDEV`, so
   `move_no_replace` copies it (`copy_exclusive`, with `fsync`), reads the copy again to prove
   it, then removes the original. With `--delete`: the comparison, then `unlink`.

Measured on the Windows share (WSL's `/mnt/c`, 2026-10-14, real photos): one reader gets 105
MB/s, four readers 454 MB/s, sixteen 468 MB/s. 0138 measured the copy fallback at ≈ 43 MB/s of
file size (420 files, 3.0 GB, ≈ 70 s, one at a time). Estimate for a copy of 2.8 MB: ≈ 53 ms to
compare (5.6 MB read) + ≈ 65 ms to move ≈ 120 ms. A collection of 300,000 photos with 30 %
copies: ≈ 3 hours, or ≈ 1.3 hours with `--delete`. Parallel writes through the share were not
measured (Claude reads `C:\Photos` only).

0150 asks whether the quarantine should sit on the same mount (then a move is a rename, and
only the comparison is left). This TODO is useful either way: the comparison alone reads 2 ×
the size of each copy.

## What to do

1. Handle up to K files at once (start with K = 4: reading scales almost ×4 from one to four
   readers, barely beyond). Each file keeps its own sequence, unchanged: journal `pending`,
   comparison, move, journal `done`. The comparison stays right before its own move: the
   safety rule ("compared again with the kept one before ...") holds per file.
2. The journal gets one writer (a lock, or a single writer the workers hand their entries to).
   Entries are already per sequence number, and `undo` judges each `pending` entry alone
   (`_never_happened` checks whether the file is still in place), so several `pending` entries
   after a crash should already be handled. Prove it with a test, for resume (`done_states`)
   and for `undo`.
3. Two copies of the same kept file may be compared at the same time: both only read it, and a
   kept file never moves during a clean.
4. Ctrl+C and `docker stop` (SIGTERM → `KeyboardInterrupt`, 0143): no new file starts; the
   files under way end as today when interrupted (a partial copy is removed by
   `copy_exclusive`). The summary counts stay exact.
5. Same for near duplicates and burst shots (`_quarantine_near`, `_quarantine_burst`).
6. Measure on a Windows test folder with a few thousand copies: K = 1 against K = 4, with and
   without `--delete`. Keep the K that helps; no setting.

## Acceptance

- Integration test: K files in flight, every entry `pending` then `done`, the same outcome as
  one at a time; a run interrupted with several `pending` entries is undone completely.
- The figures of item 6 in the commit message.

## Status — PARTIAL (2026-10-14)

### Done
- `actions/parallel.py`: `run_all` hands the actions of a clean to 4 worker threads
  (`WORKERS`), at most 8 handed out ahead; each file keeps its own sequence (journal
  `pending`, comparison, move, journal `done`), so the comparison stays right before its own
  move. The screen (current file, bar by bytes) is updated from the calling thread only.
- Near duplicates, burst shots and broken files go through the same runner; orphan sidecars
  run last and one by one (a sidecar is an orphan only once its files are gone).
- Thread safety: `JournalWriter.record` and the sequence numbers and counters of
  `JournaledChanges` are under a lock.
- Ctrl+C / `docker stop`: files not started are cancelled, the ones under way end, then the
  interruption goes on as before (journal closed, exit 130).
- Tests: `tests/unit/test_clean_parallel.py` (at most K at once, shown by the caller, a stop
  starts no new file); `test_several_actions_stopped_at_once_are_each_judged` (undo of a run
  stopped with several `pending` entries). The clean, undo and journal tests pass unchanged.

### Not done
- Item 6, the measurement on a Windows test folder (K = 1 against K = 4, with and without
  `--delete`), and choosing K from it.
  **Reason:** needs the maintainer's Docker Desktop and a folder where writing is allowed (the
  devcontainer only reads `C:\Photos`). To compare, set `WORKERS` to 1 in a local build.
