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
