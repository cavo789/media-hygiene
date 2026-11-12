# 0705 — Events found in folders: faster at scale (1.8 s at 100,000 files)

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/span_events.py`, `src/media_hygiene/search/found_desk.py`

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0678 (commit e86bce34) measured the events found in folders at 0.19 s / 1.8 s / 5.5 s for
10k / 100k / 300k files (devcontainer, warm, median of 5). Decided: a TODO per slow route.
Profile first, then do less work.

## Acceptance

- [ ] The profile's finding written here; `bench_pages` before / after
- [ ] Same events as before (equivalence test)

## Result (2026-11-12)

Profile (cProfile, 100,000 files): `event_folder_of` (a `PurePosixPath` and `shape_of` on
every slice of every file's parts) took 18.5 of 20.9 s over 5 runs. Now read once per folder
(`FolderPlaces`). Measured, `bench_pages 100000`, warm median of 5: 1,430 ms → 491 ms
(−66 %); answer byte-identical (514,533 bytes). Left: `read_days_again` (sidecar days, a
`Path` per row, about half of what remains under the profiler). Equivalence:
`test_event_folder_read_once_per_folder_says_the_same`.
