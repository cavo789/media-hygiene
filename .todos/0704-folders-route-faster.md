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
