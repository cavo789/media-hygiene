# 0722 — Face grouping: measure float16, then an approximate search, at 100k files

- **Priority**: Medium
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/faces/neighbours.py`, `src/media_hygiene/faces/cluster.py`, `src/media_hygiene/services/people_groups.py`, `tests/measure/pages/bench.py`, `tests/unit/test_faces_cluster.py`

Follows PARTIAL 0693 (`.todos/PARTIAL/PARTIAL_0693-face-grouping-all-pairs-grows-quadratically.md`, commit 4c45bc0d): the exact search went from 27.5 s to 13.5 s on the people page at 100,000 files (measured), but the acceptance of 5 s is not met because the product is still O(faces^2). Alternatives left: float16, or an approximate search (multi-index hashing, k-means cells).

Decided by the maintainer in the review of 2026-11-12.: measure first, then he decides with the figures.

## What (method: skill `measure-before-ranking`)

- Synthetic data at 100,000 files (the `tests/measure/pages` bench), devcontainer, `nice -n 19`, `PYTHON_CPU_COUNT=4`, a light load, min of 3 runs.
- Measure A: float16 embeddings with the exact search. B: an approximate search. For each: time and peak memory (`/usr/bin/time -f '%e s %M KB'`) and the **share of faces that change group** against the exact result.
- Every figure labelled *measured* (what, where, how) or *estimated*. Synthetic faces may cluster unlike real ones: say so.
- Write the table in the TODO and stop: no product change until the maintainer chooses.

## Acceptance

- [ ] Table: time, memory, share of faces changing group, exact vs float16 vs approximate.
- [ ] A recommendation, and whether a tolerance should be a setting (rule: few settings).
