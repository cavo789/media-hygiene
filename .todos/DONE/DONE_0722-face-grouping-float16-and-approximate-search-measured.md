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

## Measured (2026-11-13)

Devcontainer, `nice -n 19`, `PYTHON_CPU_COUNT=4`, `OPENBLAS_NUM_THREADS=4`, load average
0.5–2.4; `faces.cluster.face_labels` alone on 52,000 synthetic faces (100,000 files x 0.52, as
`tests/measure/pages/library.py`), its `neighbours` swapped by the variant (script kept out of
the repository: a scratch file of the session). Two data sets: **bench** (60 people, noise
0.035 per dimension, the bench's own: very tight groups) and **hard** (2,000 people, noise
0.075: pairs near the 0.363 threshold, one face in five a stranger seen once). Synthetic faces
cluster unlike real ones: real SFace vectors were not reachable here.

| Variant | Grouping time (bench / hard) | Peak memory (bench / hard) | Faces changing group (bench / hard) |
|---|---|---|---|
| Exact float32 (today) | 4.45 s / 3.67 s | 359 MB / 208 MB | — |
| float16 stored, product in float32 | 4.40 s / 3.74 s | 376 MB / 232 MB | 0 % / 0.012 % |
| float16 product (numpy, no BLAS) | ~485 s (one block of 256: 2.39 s, x203; float32: 0.013 s) | — | not run |
| Approximate: k-means cells (228 cells, 8 probed, numpy prototype) | 5.79 s / 5.56 s | 404 MB / 238 MB | 0 % / 4.0 % |

Split of the exact grouping, min of 3 runs (bench): neighbour search 2.79 s (of which the
matrix products ~2.2 s: 203 blocks x ~0.011 s), graph 0.3 s, label spreading (`_whispers`,
a Python loop) 1.42 s. Measured.

## Recommendation

- Neither: float16 gains nothing in time (numpy has no half-precision BLAS: storing in
  float16 and multiplying in float32 is the same product; multiplying in float16 is ~180x
  slower) and ~13 MB of vectors in memory; the cell search is slower in numpy at this size
  and moves 4 % of the faces on the hard set.
- The grouping is ~4.5 s of the 13.5 s of the people page cold at 100,000 files (0693): the
  other ~9 s are elsewhere (loading the faces from the index, building the board): profile
  the page with `py-spy` before touching the search. The label spreading (1.4 s) is the next
  cost inside the grouping.
- No tolerance setting: nothing approximate is proposed (rule: few settings).
