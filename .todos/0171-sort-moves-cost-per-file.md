# 0171 — `sort`: the moves cost 9 ms per file on Windows, undo 3.8 ms

- **Priority**: Medium — `sort` of 8,000 files: the moves are 73 s of 95 s (measured, `measures-20261015-1731`)
- **Batch**: journal
- **Depends**: —
- **Files**: `src/media_hygiene/actions/journal.py`, `src/media_hygiene/actions/sort_moves.py`, `src/media_hygiene/actions/no_overwrite.py`, `src/media_hygiene/actions/journaled.py`, `tests/measure/mh-measure.ps1`

## Context

After 0170, `sort` of 8,000 files (4,755 MB) on the maintainer's machine (Windows + Docker
Desktop) shows `Time per step: … moves 1 min 13 s …` out of a 95.2 s run, i.e. ≈ 9 ms per
file (measured, step 7b; one at a time, 7d: 82 s). `undo` of the same sort moves the same
8,000 files back in 30 s, ≈ 3.8 ms per file (measured, 7c). Something the sort does per file
costs ≈ 5 ms that the undo does not, or does less often.

Known per file, to measure, not assume (skill `measure-before-ranking`):

- The journal: `JournalWriter.record` does `flush` + `os.fsync` for every entry, `pending` then
  `done`: 2 fsyncs per file, under a lock shared by the 4 workers (so the fsyncs do not overlap).
  Where `/journal` lives on the maintainer's machine (a bind mount of a Windows folder or a
  named volume) decides what an fsync costs: to check in `mh-measure.ps1`'s mounts.
- 4 `stat` calls per file in the moves (32,003 for 8,000, measured in the devcontainer, 0170),
  at ≈ 0.5 ms each on the share (measured, 0170) ≈ 2 ms per file, estimated.
- The move itself: rename, or link + unlink (0138), plus a folder creation per new folder.
- In the devcontainer (local disk), the moves took 54 s for 8,000 files (≈ 6.7 ms each,
  measured, 0170): the cost exists without the Windows share, which points at the journal's
  fsyncs rather than at the share. To confirm.

## What to do

1. Measure in the devcontainer first: the same 8,000-file tree as 0170 (synthetic JPEGs,
   `sort --yes` in process), time and count per file the journal writes and fsyncs, the
   stats, the renames/links; then the same for `undo`, to see what it skips.
2. Cut what dominates, keeping every guarantee: a move is never done without its `pending`
   entry on disk first (write-ahead), and `undo` must be able to rebuild everything after a
   crash. Candidates to weigh, not pick blindly: an fsync per batch of entries already
   written (group commit, the `done` entries), `os.fdatasync`, reusing a stat the move
   already made.
3. Add a step to `mh-measure.ps1` only if the existing 7b/7c/7d lines cannot show the
   gain (the stage line already shows `moves`).

## Acceptance

- What the 5 ms per file are is explained by measurement (devcontainer, then 7b on Windows).
- If something is cut: an equivalence or crash test per change (a journal cut after a
  `pending` entry still undoes), and 7b before → after measured on Windows.
- Say whether a new setting is needed (e.g. how many entries per fsync).
