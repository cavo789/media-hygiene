# 0814 — Face links kept in the index: a cold people page compares only new faces

- **Priority**: High
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/faces/neighbours.py`, `src/media_hygiene/faces/cluster.py`, `src/media_hygiene/index/`, `src/media_hygiene/services/people.py`

Found by 0794 (profile of the people page cold open).

Measured (0794, pages bench `tests/measure/pages/bench.py`, 100,000 synthetic files, 50,347 faces, devcontainer, `nice -n 19`, `PYTHON_CPU_COUNT=4`): the people page's cold open takes 11.8 s (15.1 s under `py-spy record -r 50`). Under py-spy, 11.0 s of 14.9 s (74 %) is `faces/neighbours.neighbours`, every face against every face: the matrix product 4.4 s, the threshold compare 2.0 s, the per-row floor partition (`_floor`) 2.0 s, `flatnonzero` 1.2 s, `_closest` 0.7 s. That work is quadratic in faces and is redone from scratch at every cold open although the faces did not change.

Do: keep each face's kept links (face, neighbour, similarity; at most `NEIGHBOURS` = 30 per face) in the index, keyed by the face rows and the model; at the next build compute links only for the faces added since (new × all, plus the old faces' rows updated where a new face enters their 30 closest), forget the links of removed faces. Equivalence test: the incremental links equal a full `neighbours` run on random vectors, with ties, after adds and removals.

Gain, estimated from the measures above: cold open with no new face 11.8 s → about 1.5 s (the rest of the build, ~20 % of the profile: plan 1.8 s, whispers 1.0 s under py-spy); after 1,000 new photos (~520 faces) the neighbour step costs about 1 % of today's (520 / 50,347 rows). Storage, estimated: 50k × 30 links × ~24 bytes ≈ 36 MB in the index; say whether a cap is needed.
