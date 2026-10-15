# 0163 — `sort`: move several files of a group at a time

- **Priority**: Medium — `sort` of 4,000 files by link takes 51 s on Windows (measured, `measures-20261014-2203`), ≈ 13 ms per file of pure latency
- **Batch**: journal
- **Depends**: 0161
- **Files**: `src/media_hygiene/actions/sort.py`, `src/media_hygiene/actions/sort_moves.py`, `src/media_hygiene/actions/parallel.py`, `tests/integration/test_sort_moves.py`, `tests/measure/mh-measure.ps1`

## Context

0161 made `undo` run its actions through `actions/parallel.run_all` (4 workers), `sort` undos
included. `SortExecutor` still moves one file after the other. Its design question (0161) is
answered: it can use the same runner, group by group.

## What to do

1. Per group, in the calling thread and in this order: `free_names` (already decided before any
   move), then `Relocator.make_folder(group.folder)` (folders created and journaled in order,
   parents first) — only then hand the group's moves to `run_all` (`Runner` is generic).
2. The sidecars of a group in a second `run_all` after its files (a sidecar moves only once all
   its owners moved).
3. Thread safety: `Relocator.move` updates `Tally` (`done`, `bytes_done`) and
   `SortExecutor._moved`/`skipped`/`failed` without a lock today: put them under one (as
   `JournaledChanges`). `make_folders` inside `move` must find the folder made already (no
   two threads creating it): keep step 1 before the run.
4. Ctrl+C is honoured between groups today: keep it (a group's files under way end; the next
   group is not started); `MoveOutcome.interrupted` unchanged. Check that `manifest` and the
   plan's `sort-decisions`/`moved` lists do not depend on the order of `_moved` (the `done`
   lines may come in another order than the `pending` ones).
5. Add a step to `tests/measure/mh-measure.ps1` timing `sort` again (the 4,000-file step).

## Acceptance

- *Estimate*: `sort` of 4,000 files 51 s → about 15–20 s (the 4 workers of `clean` cut its time
  by ≈ 65 %, 0149/0161), measured on the maintainer's machine.
- Tests: at most `WORKERS` moves at once; names taken decided before the moves (two files of one
  group with the same name never race for it); an interrupted sort resumed; its undo unchanged.

## Status — DONE (2026-10-15)

- Groups (a file and its companions) move a few at a time through `run_all`, names decided
  first in order (`actions/sort_groups.py`), counters locked, folders made once under a lock,
  `moved` sorted by journal `seq`; tests in `tests/integration/test_sort_parallel.py` and
  `tests/unit/test_sort_groups.py`.
- Measured here (simulated 13 ms per rename, 400 files): 8.2 s → 2.6 s (−69 %).
- Left for the maintainer: the Windows timing (7b: 4 at once, 7d: one at a time). The script
  is in the repository, not on the PC: fetch it first, the image built from this branch.

  ```powershell
  cd C:\temp
  Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/main/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1
  powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 7 -Count 4000
  ```

## Windows measurement (2026-10-15)

Measured by the maintainer (`measures-20261015-1429`, `-Only 7 -Count 4000`: 8,000 files,
4,755 MB, Docker Desktop, image built from `iterate/2026-10-15`; one run of each, 7b before 7d):

| Step | `Duration` (moves) | Wall time (`docker run`) |
|---|---|---|
| 7d `sort`, one at a time (`[clean] workers = 1`) | 1 min 22 s (10.3 ms/file) | 125.1 s |
| 7b `sort`, 4 at once (default) | 1 min 10 s (8.8 ms/file) | 111.8 s |
| 7c / 7e `undo` of the sort (default 4) | 28 s (3.5 ms/file) | 31.3 / 31.9 s |

- `sort`'s moves: 82 s → 70 s, **−15 %** (measured), far from the −69 % estimated from the
  simulation: Docker Desktop's renames and links overlap much less than its reads (0149). The
  estimate was wrong; 4 workers still help, so they stay.
- `undo` of a sort: 9.3 ms/file on 2026-10-14 (37 s for 4,000, one at a time) → 3.5 ms/file
  (−62 % per file; different runs and sizes: indicative). That is 0161's gain.
- About 42 s of each `sort` run fall outside `Duration` (wall 111.8 s against 70 s), against
  ≈ 3 s for `undo`: now larger than what the workers saved. Followed by 0170 (filed as 0168, renumbered: main had a 0168).
