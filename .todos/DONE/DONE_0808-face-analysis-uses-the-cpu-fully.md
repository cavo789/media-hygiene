# 0808 — Face analysis uses the processor fully: time split measured, threads tuned

- **Priority**: High
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/faces/onnx_runner.py`, `src/media_hygiene/faces/worker.py`, `src/media_hygiene/services/people.py`, `src/media_hygiene/services/runtime.py`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: the run on 100 of their own photos (a step of `tests/measure/mh-measure.ps1`), Windows + Docker Desktop

Filed by the speed review of 2026-11-13. Decided by the maintainer the same day: **no GPU
image** (a `:gpu` variant was rejected: several GB and a second image to maintain); only
free changes, same image, same dependencies.

## Context

`mh people` (and `audit --people`) runs one process per CPU (`process_pool`); each one
decodes a photo, then runs the two ONNX models with `intra_op_num_threads = 1`
(`onnx_runner.py`). Nobody measured where a photo's time goes: the decode (Pillow, a
3–4 MB JPEG, HEIC tiles) or the models. A first run on a large library takes hours.

## Proposal

- Measure first, per photo, on synthetic photos shaped like phone photos (devcontainer)
  then on 100 of the maintainer's (read-only mount): decode + resize, detection,
  alignment, embedding; then the whole run at 1, 4, 8, 16 workers.
- Variants, one at a time, kept only on a measured gain ≥ 10 %: fewer workers with
  2–4 ONNX threads each; `graph_optimization_level = ORT_ENABLE_ALL` and a saved
  optimised model in `/cache/models`; Pillow `draft()` mode for JPEG (decode at reduced
  size directly, as the detector needs far less than full resolution); decode of the next
  photo overlapping the models of the current one.
- Equivalence: the same faces (boxes within a pixel, embeddings cosine ≥ 0.999) on the
  test photos before and after.

## Acceptance

- [ ] The time split per step and the worker/thread table, *measured*, in this TODO's status
- [ ] Each kept variant: before/after photos per second, and the equivalence test
- [ ] A new limit (workers, threads): say whether it should be a setting (`few-settings`)

## Where the user gains

Unknown until measured: a first full analysis of the library faster by the measured
factor; nothing else changes (pages are not concerned).

## Progress (2026-11-14)
- Step 49 of `mh-measure.ps1` written (`-Only 49 -Count 1`): 100 random JPEG/HEIC of
  `C:\Photos` read-only, per photo decode / detect / embed / turn guess, a 1280 px decode
  compared (faces counted both ways), then photos/s for processes x ONNX threads
  (4x1, N/2x1, Nx1, N/2x2, N/4x4). Checked in the devcontainer on 12 synthetic photos.

## Measured on the maintainer's PC (2026-11-14, step 49, 100 random photos, 3.0 MB average, 16 CPUs)
- One process, ms per photo: turn guess 65, decode 65, find 35 (detect 18, embed 10,
  alignment ~7); total ~165 ms. A 1280 px decode: 37 ms instead of 65, same face count on
  98 of 98 photos (46 faces both ways; boxes and vectors not compared yet).
- Processes x ONNX threads, photos/s: 4x1 22.1, 4x4 13.1, 8x1 37.6, 8x2 25.5, 16x1 **43.1**.
  The current setting (one process per CPU, one thread each) is the fastest: no thread
  change, no setting.
- Left to try, each worth >= 10 % (*estimated* from the split): the turn guess on a reduced
  picture (65 ms, 39 %), the 1280 px decode (-28 ms, 17 %), with the equivalence test
  (boxes within a pixel scaled back, cosine >= 0.999).

## Variant 1 implemented (2026-11-14): the turn guess on a reduced copy
- `turn_of` turns a copy at most `GUESS_EDGE` (2 x the detector's 640) wide instead of the
  full picture. Test `test_turns_are_guessed_on_a_reduced_copy`. Step 49 now also runs the
  old full-size guess on the same photos (`turn_full_size`) and prints 49e: same turn on
  N of M photos guessed — the equivalence proof, on the maintainer's photos.
- Waits for: step 49 on an image built from this commit (expected `turn` 65 → ~15 ms,
  *estimated*; kept only if 49e shows the same turns).

## Variant 1 measured (maintainer's PC, step 49, 2026-11-14 22:17, image of a978b683)
- Turn guess 61 → 52 ms per photo (-15 %), same turn on 60 of 60 photos guessed. Smaller
  than estimated: the three detections themselves are ~51 ms (17 ms each), the full-size
  turning was only ~9 ms of it. Kept (equivalent, cheaper).
- Throughput 16x1: 43.1 → 52.7 photos/s (+22 %), but the other rows moved +7 to +9 %
  between the two runs (noise, a warmer disk): the part due to the change is ~+10 %.
- Not done, a decision: the 1280 px decode (56 → 37 ms, same face count on 98/98) changes
  the pictures the vectors are computed from; vectors not compared yet (cosine >= 0.999
  needed, else the groups already named may move).

## Closed — DONE (2026-11-14)
- The maintainer's decision: the 1280 px decode (~12 %) is not worth the risk to the
  named groups; not pursued. Threads: one per process stays (fastest, measured). No setting.
