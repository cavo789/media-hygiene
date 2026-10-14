# 0151 — A first audit of 300,000 files: bound the work in flight, not one task per file at once

- **Priority**: Medium — measured ≈ 4.4 KB per file of peak bookkeeping: ≈ 1.3 GB for 300,000 files, ≈ 4.4 GB for a million, on top of the facts themselves; Docker Desktop gives the Linux VM half the RAM by default, and an out-of-memory kill restarts nothing
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/scan/broken.py`, `src/media_hygiene/scan/file_check.py`, `src/media_hygiene/scan/exact.py`, `src/media_hygiene/scan/video_prints.py`, `tests/integration/`

## Context

Speed and cache review of 2026-10-14 (third pass), for collections of several hundred thousand
files.

- `BrokenFileFinder._run` creates one task per file to check, all at once, in one `TaskGroup`,
  and `FileChecker._in_pool` hands each picture to the process pool at once
  (`loop.run_in_executor`, no limit): the pool queues one work item, one future and one
  asyncio future per file, for the whole first audit.
- `ExactDuplicateFinder._digests` creates one task per file to hash (the semaphore limits the
  reading, not the tasks); `VideoPrinter.looks` one per video.

Measured in the devcontainer (Python 3.14, 100,000 tasks waiting on one gate, then handed to a
pool, `tracemalloc`): 1.6 KB per waiting task, **4.4 KB per file at the peak** once all are
submitted. The facts kept for the audit add ≈ 3 KB per file (listing entry 330 B, `MediaFile`
450 B, `MediaMetadata` 1.7 KB, `VisualFacts` 230 B): ≈ 0.9 GB for 300,000 files.

| Files | Facts (warm audit) | + bookkeeping of a first audit |
|---|---|---|
| 300,000 | ≈ 0.9 GB | + ≈ 1.3 GB |
| 1,000,000 | ≈ 3 GB | + ≈ 4.4 GB |

Killed for lack of memory, the run keeps what it committed (0143), but every new run dies at
the same point.

## What to do

1. Replace "one task per file" with a fixed number of workers pulling from one iterator (or an
   `asyncio.Queue`), in `BrokenFileFinder._run`, `ExactDuplicateFinder._digests` and
   `VideoPrinter.looks`. For pictures: about twice the pool's processes in flight, so that the
   pool never waits. For reading: `Sizes.IO_CONCURRENCY`. Same results, same order of the
   findings (they are sorted afterwards), same progress bar and ETA.
2. Ctrl+C and `docker stop` stop as today: no new file is taken, the files under way end and
   are stored.
3. Not in this TODO: making the facts smaller. `MediaMetadata` (pydantic) is 1.7 KB of the 3 KB
   per file. Revisit only if a collection of a million files is a target: a slotted
   dataclass, or interned strings (make, model, lens repeat across files).

## Acceptance

- Integration test with many small fake files (or a fake checker): the number of tasks and of
  pending pool items stays bounded (e.g. under 4 × the workers) during the pass; the same
  findings as before.
- Peak memory of a first audit of a synthetic tree (≥ 50,000 small files, `tracemalloc` or RSS)
  before and after, in the commit message.
