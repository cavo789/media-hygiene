# 0693 — The people page's first grouping compares every face with every face

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/faces/cluster.py`, `src/media_hygiene/services/people_groups.py`, `tests/unit/test_face_cluster.py`

Filed by 0678 (the pages' speed budget).

## Context

`faces/cluster.py` `_neighbours` finds each face's 30 nearest neighbours by a full
`vectors[block] @ vectors.T` against every face: O(faces²). It runs on the people
page's first opening (and after a threshold change), then the labels are kept
(`services/people_labels`).

Measured (devcontainer, i9-14900K capped, `nice -n 19`, `PYTHON_CPU_COUNT=4`,
`python -m tests.measure.pages.bench`, synthetic index, 0.52 face per file):

| Files | Faces (about) | `GET /people/` first | next openings |
|---|---|---|---|
| 10,000 | 5,000 | 0.96 s | 0.34 s |
| 100,000 | 50,000 | 27.3 s | 3.7 s |
| 300,000 | 155,000 | not run (estimated ≈ 250 s: × 9 from 100,000) | — |

×10 files gives ×28 on the first opening: quadratic. The maintainer's library (52,094
files, 27,159 faces, measured 2026-10-17) is estimated ≈ 8 s from these figures.

## Proposal

- Cut the candidates before the product: an approximate nearest-neighbour search
  (random projections / multi-index hashing as `plan/near` does, or a coarse k-means
  partition visiting the closest few cells), numpy only; or at least compare in
  float16 with BLAS on several threads.
- Prove equivalence: same groups as the brute force on random clustered vectors (keep
  the brute force as the test's reference), ties included.
- Bench before / after with `bench_pages` (the people page row of `tests/measure/pages-budget.md`).

## Acceptance

- [ ] First opening at 100,000 files ≤ 5 s measured, groups identical on the test sets

## Where the user gains

A large family library (150,000+ faces) opens the people page in seconds instead of
minutes the first time (estimated from the table above).

## Status — PARTIAL (2026-11-12)

- **Done:** exact neighbour search in `faces/neighbours.py`: only the faces above the
  threshold, each row bounded by the k-th closest of its first 8,192 columns, cut to the
  closest on a small array; buffers reused. Equivalence test
  `tests/unit/test_faces_neighbours.py` (full-sort brute force, ties at the last place: first
  row, exact copies included). People page cold at 100,000 files 27.5 s → 13.5 s (measured,
  `tests.measure.pages.bench`, load average 6–9).
- **Not done:** ≤ 5 s. **Reason:** the all-pairs product stays; an approximate search or
  float16 gives near-identical groups only — the maintainer decides if that is acceptable.
