# 0703 — Places page: read only the index rows with GPS (5.2 s at 100,000 files)

- **Priority**: Medium
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/services/places_index.py`, `src/media_hygiene/services/places_build.py`, `src/media_hygiene/index/`

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0678 (commit e86bce34) measured the places page at 0.47 s / 5.2 s / 14.8 s for 10k / 100k / 300k
files (devcontainer, warm, median of 5): it reads every index row although 1.3 % carry GPS;
72 % of its time there (py-spy at 100k). Decided: a TODO per slow route.

## Acceptance

- [ ] A query reading GPS rows only (an index on them if needed, schema upgrade in place)
- [ ] `bench_pages` before / after, figures in `tests/measure/pages-budget.md`; same clusters (equivalence test)
