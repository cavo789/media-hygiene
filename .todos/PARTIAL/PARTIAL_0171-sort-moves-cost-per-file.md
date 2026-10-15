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

## Status — PARTIAL (2026-10-15)

### Done
- Measured in the devcontainer (8,000 synthetic 160×120 JPEGs, 64 MB, 200 folders, local
  disk; `audit`, `classify`, then `sort --yes` and `undo --yes` run in process, every
  `os.fsync`/`os.stat`/`os.lstat`/rename/`JournalWriter.record` counted and timed):
  - `sort`, moves 52.6 s: **16,832 `fsync` in 50.3 s (≈ 3.0 ms each, 96 % of the stage)**,
    serialized by the journal's lock; the renames 0.35 s, the 40,465 stats 2.0 s, the JSON
    0.2 s.
  - `undo`, 52 s: 16,832 `fsync` in 49.0 s, 48,654 stats 1.5 s, the moves 0.56 s.
  - Here, `sort` and `undo` cost the same per file (≈ 6.5 ms), both bound by the journal's
    two syncs per file. The Windows gap (9 ms against 3.8 ms) is therefore not the journal
    alone: to see on Windows (below).
- Cut (`actions/group_commit.py`, new; `JournalWriter.record`): a `pending` line still
  returns only once an `fsync` started after it was written has ended (write-ahead kept);
  while one `fsync` runs, the other workers' lines wait for the next one, which covers them
  all (group commit). A `done` line is not synced on its own: the next `fsync` or the one
  made when the journal closes carries it. Lost in a power cut, it leaves its action
  `pending`, which `undo` (`_never_happened`, the file judged on disk) and a resumed `sort`
  (`sort_resume`, "pending but carried out") already handle — no new state.
  - Measured, same tree: `sort` moves **52.6 s → 12.1 s (−77 %)**, 16,832 → 3,763 `fsync`;
    `undo` **52 s → 14 s (−73 %)**, 16,832 → 4,284 `fsync`; 8,000 files back after undo.
  - Tests: `tests/unit/test_group_commit.py` (a `pending` line is on disk when `record`
    returns, a `done` one waits; 4 workers on a slow `fsync`: fewer syncs than lines, no
    line returned before being synced); `test_a_sort_whose_done_lines_were_lost_is_undone_completely`
    (`tests/integration/test_undo_sort.py`: a journal with only its `pending` lines, as a
    power cut could leave it, still undoes everything).
- `os.fdatasync`: not used — an appended line changes the file size, which `fdatasync` must
  sync too on Linux; little to gain, and unknown on Docker Desktop's mounts.
- Setting: none needed — the batch is whatever the workers wrote during the previous `fsync`
  (`[clean] workers` already bounds it).
- `mh-measure.ps1`: unchanged; 7b (`moves` in `Time per step`), 7c and 7d already show the gain.

### Not done
- The Windows measurement: 7b/7c/7d before → after (before, `measures-20261015-1731`:
  7b moves 1 min 13 s of 95.2 s, 7c undo 30 s), and with it what the remaining ≈ 5 ms per
  file of `sort` against `undo` are on Docker Desktop. *Estimated* gain on Windows: if the
  journal's `fsync` on the bind-mounted `tool\journal` costs about what `undo` suggests
  (≤ 30 s / 16,000 ≈ 1.9 ms), up to ≈ 16,000 × 1.9 ms × 0.77 ≈ 23 s less on 7b.
  **Reason:** only the maintainer's PC has Windows + Docker Desktop. With an image built
  from `main` after this change:
  ```powershell
  cd C:\temp
  Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/main/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1
  powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 7 -Count 4000
  ```
  If 7b's `moves` stays far above 7c, the next suspects are per-file calls on the NTFS
  share that `sort` makes and `undo` does not (`lexists` of the target, the link fallback
  of 0138): step 8 runs them one by one (it may need a timing per operation).
