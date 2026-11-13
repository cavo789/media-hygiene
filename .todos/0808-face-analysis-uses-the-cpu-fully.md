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
