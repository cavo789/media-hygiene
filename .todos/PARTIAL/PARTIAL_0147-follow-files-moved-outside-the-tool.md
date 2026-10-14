# 0147 — Files moved or renamed outside media-hygiene keep their cached work

- **Priority**: High — renaming one folder in Explorer today throws away its decoding, video fingerprints, faces and, worst, the vision model's descriptions (hours of model time)
- **Batch**: index
- **Depends**: 0146, 0148
- **Files**: `src/media_hygiene/index/pruning.py`, `src/media_hygiene/index/repository.py`, `src/media_hygiene/scan/file_check.py`, `src/media_hygiene/scan/broken.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/services/classify.py`, `documentation/en/start/02-keep-the-cache.md`, `documentation/fr/start/02-keep-the-cache.md`, `tests/integration/`

## Context

Speed and cache review of 2026-10-14 (third pass), for collections of several hundred thousand
files. Every table of the index is keyed by path: `files` (integrity, visual facts, metadata,
digests, video fingerprints), `descriptions`, `tags`, `face_scans`, `faces`, `measures`. `sort`
and `undo` call `FactsRepository.move`, so their moves keep everything. A move made outside the
tool does not:

- a folder renamed in Explorer (`C:\Photos\2019` → `C:\Photos\2019 Vacances`), a folder dragged
  elsewhere in the mounted tree, a reorganisation by Lightroom or digiKam, a manual sort after
  reading the `classify` workbook;
- what follows: the next `audit` or `classify` walk proves the old paths gone,
  `forget_missing` deletes their rows in every table, and the new paths are checked from zero.

What that costs again, measured:

| Cached work | Cost per file |
|---|---|
| Integrity + visual facts of a 12 MP JPEG | ≈ 28 ms CPU + a full read (≈ 45 ms on one worker through the Windows share) |
| Same for a HEIC | ≈ 400 ms CPU (0155) |
| Video fingerprint | 0.5–1.8 s CPU per 1080p video (0141) |
| Vision model description (`tags`, `classify`) | 1.9–3.5 s per photo (benchmark of 2026-10-10) |
| Faces (`people`) | one decode + two ONNX models, half the CPUs |

Renaming a folder of 10,000 described photos: about a minute of decoding on 16 CPUs, and 5 to
10 hours of model time to describe them again. Explorer keeps the modification time of a file
it moves or copies, so (size, mtime_ns) survives such a move, and the content proves the rest.

## What to do

1. **Every row gets its partial digest** (first and last 64 KiB, `scan/hashing.partial_digest`).
   0148 computes it for every picture it checks. Videos: compute it at their check (a 128 KiB
   read next to `ffprobe`). Rows indexed before: fill it once, as the one-time metadata pass
   does (`Need.METADATA` in `scan/file_check.py`), with its own progress step ("Reading 128 KB
   of each file already in the cache, once"). Measured scale: 52,000 files × 128 KiB = 6.6 GB,
   about 15 s at the 460 MB/s the Windows share gives four readers or more.
2. **`forget_missing` pairs before it forgets.** Gone rows (under the walked roots, as today)
   and listed files the index does not know are paired on (size, mtime_ns). Each pair whose
   partial digest matches (128 KiB read of the new file) is moved with `FactsRepository.move`
   (every table, and the `moves` record of 0146 so that the names follow). The other gone rows
   are forgotten as today. Never pair on (size, mtime_ns) alone.
3. Both `audit` and `classify` get it (both call `forget_missing`).
4. One console line (pedagogy rule), e.g. "1,234 files moved or renamed since the last audit:
   what the cache knew follows them." Nothing when there is none.
5. Optional, decide while implementing: a collection mounted at another path (moved to another
   drive: `/data/d/Photos` instead of `/data/c/Photos`) leaves its rows outside every walked
   root, never pruned. Those rows could lend their facts (copied, never moved nor forgotten) to
   the new files they match by size, mtime and partial digest.
6. Docs en + fr (`start/02-keep-the-cache.md`): renaming or moving folders in Explorer keeps
   what the cache knows; changing a file (a new modification time) does not.

## Acceptance

- Integration test: index a tree, rename a folder and move a file on disk, run the audit: no
  picture decoded again (counting fake), rows (facts, faces, descriptions, tags) at the new
  paths, the names of 0146 still applied.
- Two different files with the same size and mtime are never paired (different partial digest).
- A moved and then edited file (new mtime) is checked again.

## Status — PARTIAL (2026-10-14)

### Done
- Item 1: `scan/partial_fill.py` gives every checked file its partial digest once (videos,
  rows of older versions, pictures above `WHOLE_READ_LIMIT`), its own progress step, stored
  as it goes. Pictures checked since 0148 already get it from their decoding. Videos get it
  from this pass (just after their check), not inside the `ffprobe` check itself.
- Items 2–3: `index/rematch.py`: gone rows and unknown listed files paired on (size, mtime_ns,
  partial digest), never on size and time alone; among identical copies the same file name is
  preferred. `forget_missing` moves the pairs (`FactsRepository.move`: every table, and the
  `moves` record of 0146, so the names follow), forgets the rest, and returns `Pruned`
  (followed, forgotten). `audit` and `classify` both pass the listed files.
- Item 4: one console line (`services/listing.tell_followed`), translated.
- Item 6: docs en + fr (`start/02-keep-the-cache.md`).
- Tests: `tests/integration/test_follow_moved_files.py` (a renamed folder: nothing decoded
  again, faces at the new path; different content or another time: never paired).

### Not done
- Item 5 (optional): a collection mounted at another path (moved to another drive) lending
  its rows, copied, to the files it matches.
  **Reason:** deliberately left out: copying rows of every table (facts, faces, descriptions,
  tags, measures) without forgetting the originals needs its own design (which copy do the
  names of `people` point to?). Revive if a maintainer moves a collection to another drive.
