# 0678 — A speed budget for the pages: every route timed on a synthetic 100,000-file index

- **Priority**: Medium
- **Batch**: tests
- **Depends**: —
- **Files**: `tests/measure/`, `tests/support/indexed_photos.py`, `.devcontainer/scripts/helpers/`, `.github/workflows/`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

The speed work so far was done TODO by TODO, each with its own measure (0353: search 30 ms
at 100,000 files; 0442; 0588…). Nothing replays them: a page that becomes slow with the
size of the library is found by the maintainer on real photos, late. `tests/measure/` holds
the Windows script and the embeddings bench only (read 2026-11-10). The demo tree has 28
files: every route answers in ms there, whatever its growth.

## Proposal

- A generator of a synthetic index (no pictures needed: rows, tags, faces, GPS, events
  shaped like the real library — sizes from the maintainer's measured stats) at 3 sizes:
  10,000, 100,000, 300,000 files.
- A bench that starts the home server on it and times each read route the pages call
  (`/api/state`, `/api/search` with words / a period / a place, `/api/folders`,
  `/api/events`, people, places clusters, albums), cold and warm, with the peak memory.
- A table kept in the repository (`tests/measure/pages-budget.md`, *measured* figures) and a
  budget per route (e.g. warm ≤ 100 ms at 100,000); a weekly CI job or a helper `bench_pages`
  fails on a route that grew by more than 30 %.
- A profile (`py-spy`) of the slowest route at 300,000, to rank the next speed TODOs on
  figures (skill `measure-before-ranking`).

## Acceptance

- [ ] The table at 3 sizes; what grows faster than linearly is named, with a TODO each
- [ ] The helper documented in the devcontainer cheatsheet; runs gently (`nice`, 1 at a time)

## Where the user gains

Indirect: a slow page is caught before a release instead of on the family's library; the
next speed TODOs are ranked on measures.

## Status — PARTIAL (2026-11-11)

### Done

- `tests/measure/pages/library.py`: the synthetic index (schema 20, the index's own
  writers: `row_of` + `UPSERT`, `TagStore`, `FaceStore`; a sparse placeholder per file,
  the people page checks they are there; 300,000 files ≈ 30 MB of inodes, no picture).
- `tests/measure/pages/bench.py`: `home` started in-process as `mh` does, each route sent
  through its router, cold and warm (median of 5), peak memory; the 0677 warm-up is
  disabled (its `ready` callback is never called); `--skip`, `--profile`, `--out`.
- `tests/measure/pages-budget.md`: the table (measured, machine and method stated), a
  budget per route; `tests/measure/pages/budget.py` and the helper `bench_pages`
  (category Quality) fail on a route past its budget or grown by more than 30 %.
- Profiles (py-spy, 100,000): the people page's first grouping is all pairs (quadratic,
  0.96 s → 27.3 s for ×10 files): 0693. The places page reads every row of the index
  (72 % in `places_index.read_index`), linear.
- `tests/unit/test_pages_budget.py`.

### Not done

- 300,000 files, the people routes: the first opening alone is estimated ≈ 250 s (×9
  from 100,000), past the 3 minutes a run may take on the maintainer's PC; the other
  routes at 300,000 are in the table (two passes).
- The profile at 300,000: py-spy did not finish within 170 s there (its overhead on a
  14.5 s route run 6 times); the profiles were taken at 100,000.
- No weekly CI job: the 100,000 run takes ≈ 2 min of CPU on a fast PC and the figures
  of a shared CI runner differ from this table's machine, so a +30 % check there would
  fail on noise; the helper stays the gate. Possible later with its own table per runner.
