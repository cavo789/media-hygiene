# 0704 — `/api/folders`: the folder tree without walking every row (3.0 s at 100,000 files)

- **Priority**: Medium
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/search/folders.py`, `src/media_hygiene/search/folder_tree.py`, `src/media_hygiene/index/`

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0678 (commit e86bce34) measured `/api/folders` at 0.3 s / 3.0 s / 8.9 s for 10k / 100k / 300k
files (devcontainer, warm, median of 5). Decided: a TODO per slow route. Profile first
(`measure-before-ranking`), then do less work (a cached tree invalidated by the index's
`data_version`, or a grouped query).

## Acceptance

- [ ] The profile's finding written here; `bench_pages` before / after
- [ ] Same tree as before (equivalence test); every invalidation event tested if cached

## Result (2026-11-12)

Profile (cProfile, `bench_pages --profile folders`, 100,000 files): the SQL is negligible;
`folder_counts` spent its time building a `Path` per file and per parent
(`is_relative_to`, `parents`: 7.8 M `Path` items). Now text only: each file added to its own
folder, then each folder once to those above it. No cache, so no invalidation to test.
Measured, `bench_pages 100000`, warm median of 5: 2,364 ms → 137 ms (−94 %); answer
byte-identical (669,303 bytes). Equivalence: `test_text_counts_equal_the_path_counts`.
