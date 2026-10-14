# 0140 — A light forkserver for the image pool: 0.5 s before the first decode

- **Priority**: Medium — measured 0.58 s before 16 workers answer, 0.045 s once the forkserver is warm; paid by every command that decodes (audit, report, review, classify, search, people)
- **Batch**: scan
- **Depends**: 0131
- **Files**: `src/media_hygiene/services/runtime.py`, `src/media_hygiene/scan/image_check.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/services/reporting.py`, `src/media_hygiene/__main__.py`

## Context

Speed review of 2026-10-14 (second pass). Since Python 3.14, `ProcessPoolExecutor` on Linux
starts its workers with **`forkserver`** (it was `fork`). `services/runtime.process_pool`
passes no `mp_context`, so it gets that default. The forkserver process imports the parent's
`__main__` first. For `media-hygiene` that is `media_hygiene.__main__`, which imports
`cli.app`: the whole CLI, every service, numpy, openpyxl (see 0136).

Measured in `media-hygiene:latest` (16 CPUs), `ProcessPoolExecutor(initializer=
prepare_image_worker)` answering 200 trivial tasks:

| start method | time |
|---|---|
| `forkserver` (today), cold | 0.580 s |
| `forkserver`, server already running | 0.045 s |
| `fork` | 0.043 s |

That time is spent before the first image is decoded. An `audit` opens two pools
(`services/audit.py` for the checks, `services/reporting.py` for the previews). The forkserver
is reused by the second one, but the first one waits.

`fork` is not the answer: the parent already runs asyncio and `to_thread` workers, and forking
a process with threads can deadlock (Python 3.12+ warns about it).

## What to do

1. `process_pool()`: pass an explicit `multiprocessing.get_context("forkserver")` and call
   `set_forkserver_preload([...])` with only what the workers need
   (`media_hygiene.scan.image_check`, `media_hygiene.scan.raw_check`, `PIL.Image`,
   `pillow_heif`, `numpy`). Check with `-X importtime` in a worker that the server no longer
   imports `media_hygiene.cli`. Python always preloads `__main__`: check how to avoid it
   (a tiny `__main__` that imports `cli.app` only inside `main()` may be enough, which also
   helps 0136).
2. Start it early: commands that will need the pool start the forkserver in a background
   thread at command start (`multiprocessing.forkserver.ensure_running()`), so it warms up
   during the listing.
3. Workers: set `OPENBLAS_NUM_THREADS=1` (and `OMP_NUM_THREADS=1` for onnxruntime in
   `people`) in the pool's environment. numpy ships OpenBLAS with `MAX_THREADS=64`: 16 workers
   × 16 BLAS threads oversubscribe the CPU when a matrix op is large enough to go
   multi-threaded. Keep this only if it measures faster.
4. Measure with the 0131 step timings: time to the first decoded image, and the whole warm
   `audit`, before and after.

## Acceptance

- The forkserver does not import `media_hygiene.cli` (checked by a test that reads
  `sys.modules` from inside a worker).
- The first pool of a command answers in under 0.15 s on the devcontainer (measured as above).
- Ctrl+C still stops the workers at once (`_ImagePool.__exit__` unchanged).

## Status — DONE (2026-10-14)

- `process_pool` uses an explicit `forkserver` context whose preload list is only
  `scan.image_check`, `scan.raw_check` and `pillow_heif` (`__main__` is no longer preloaded).
- The bigger cost was elsewhere: every forkserver child imports the main script again as
  `__mp_main__`, and `media_hygiene/__main__.py` imported the whole CLI at the top. It now
  imports it inside `main()`: a worker loads `media_hygiene.constants` only.
- `Runtime.warm_pool()` (no-op with the tests' thread pool) starts the fork server in a
  background thread at the start of `AuditService.run`: Pillow and numpy load during the listing.
- Measured in the devcontainer (16 CPUs, 200 trivial tasks, a script shaped like the console
  script): before, first pool 0.51 s / second 0.32 s; after, cold 0.20 s / 0.047 s, and
  **0.05 s** when warmed during the listing.
- `tests/integration/test_image_pool.py`: a worker of a pool made under a `__main__` that loads
  the CLI holds no `media_hygiene.cli` module (it failed before the `__main__` change).
- Not done: `OPENBLAS_NUM_THREADS` / `OMP_NUM_THREADS` (item 3), to keep only if it measures
  faster, which needs real photos (0104); the whole warm `audit` before/after (0104 §7).
