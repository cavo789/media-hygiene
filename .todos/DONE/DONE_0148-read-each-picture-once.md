# 0148 — First audit: read each picture once, its digests computed by the worker that decodes it

- **Priority**: High — on a Windows folder the first audit is bound by reading, and every exact duplicate is read twice in full today
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/scan/image_check.py`, `src/media_hygiene/scan/raw_check.py`, `src/media_hygiene/scan/file_check.py`, `src/media_hygiene/scan/hashing.py`, `src/media_hygiene/scan/exact.py`, `src/media_hygiene/index/facts.py`, `tests/unit/`, `tests/integration/`

## Context

Speed and cache review of 2026-10-14 (third pass), for collections of several hundred thousand
files. A first audit reads every picture twice when it has a copy:

1. the integrity pass decodes it in the worker pool (`inspect_image`, `inspect_raw`): every
   byte is read (JPEG entropy data even when drafted, every RAW pixel through `raw.unpack()`,
   every HEIC tile);
2. then `ExactDuplicateFinder` reads 128 KiB of each file of a shared size, and the whole of
   each one whose partial digest matches: in practice every exact duplicate, in full, a second
   time. The integrity pass ends before this one starts, so on a large collection the second
   reading never comes from a cache.

Measured on 2026-10-14, real photos of `C:\Photos` read-only through WSL's `/mnt/c` (the 9p
sharing that Docker Desktop also uses for `C:\` folders), image built from `main`:

| | |
|---|---|
| Reading, 1 / 4 / 16 readers | 105 / 454 / 468 MB/s |
| `inspect_image(path)` today, cold, one worker, JPEG of 2.7–3.0 MB | 45.5–50.2 ms wall, 27.6–29.4 ms CPU |
| One `read()` into memory + SHA-256 of the whole file + the same work on the bytes | 40.5–46.4 ms wall, 25.9–29.4 ms CPU |
| SHA-256 alone (12 MP JPEG, 3.4 MB, devcontainer) | 1.3 ms (≈ 2.6 GB/s) |

So one read with the digest is even a little faster than today's path-based decode. And 16
workers would need ≈ 570 photos/s × 2.8 MB ≈ 1.6 GB/s to stay busy, against 0.46 GB/s from the
share: a first audit of JPEGs on Windows waits for the disk, not for the decoder. Estimate for
300,000 photos of 2.8 MB with 30 % exact duplicates: ≈ 30 min of reading for the checks, then
≈ 9 min to read the duplicates again. This TODO removes the second part.

## What to do

1. `inspect_image` and `inspect_raw`: read the file in one `read()`, compute its SHA-256 and its
   partial digest from those bytes, then decode from `io.BytesIO` (Pillow) or from a file object
   (`rawpy.imread` takes one: check it with the RAW test files). `hashing.py` gains the
   functions over bytes. They must give exactly the values of `partial_digest` and
   `full_digest` (same algorithm, same first and last 64 KiB), so the digests already in the
   index stay valid.
2. Above a size cap (e.g. 256 MB: scans, huge panoramas), keep today's decode from the path and
   leave the digests to the exact pass. Memory then stays at one file of at most the cap per
   worker; say it in a comment.
3. `ImageInspection` carries both digests; `FileChecker.check` stores them
   (`FileFacts.with_partial`, `with_full`), in the same `put` as the other facts.
4. `ExactDuplicateFinder` needs no change: it finds the digests of every checked picture in the
   index, and reads only videos, other files and pictures above the cap.
5. Videos are unchanged: never read whole.

## Acceptance

- Unit test: the digests over bytes equal `partial_digest` and `full_digest` of the same file
  (empty, under 64 KiB, between 64 and 128 KiB, large).
- Integration test: a first audit of a tree holding exact duplicates finds the same groups, and
  never calls `full_digest` for a picture the integrity pass checked (counting fake).
- Measured once on a Windows folder through Docker (a fresh cache volume over a test folder
  with duplicates): the `checks` and `fingerprints` stages of `--verbosity verbose`, before and
  after, written in the commit message.

## Status — DONE (2026-10-14)

### Done
- `scan/whole_read.py`: a picture up to `WHOLE_READ_LIMIT` (128 MB, not 256: 16 workers ×
  256 MB could reach 4 GB on a Docker Desktop VM) is read in one `read()`; `inspect_image`
  decodes it from `io.BytesIO`, `inspect_raw` from a file object (`rawpy.imread` accepts one;
  a truncated RAW gives the same LibRaw error text).
- `hashing.digests_of(bytes)` gives exactly `partial_digest` / `full_digest` (unit test over
  0, 10, 64 KiB + 10, 128 KiB and 128 KiB + 10 bytes). `ImageInspection.digests`, stored by
  `FileChecker.check` with the other facts (also for a broken picture: it was read anyway).
- `ExactDuplicateFinder` unchanged: it finds the digests in the index.
- Test `test_first_audit_reads_each_picture_once`: during a first audit of the demo tree,
  `exact.full_digest` is only called for videos.

### Not done
- The measurement on a Windows folder (acceptance item 3): the `checks` and `fingerprints`
  stages of `--verbosity verbose` on a first audit (fresh cache volume over a test folder with
  duplicates), before and after.
  **Reason:** needs the maintainer's Docker Desktop and a rebuilt image; the devcontainer
  measures (2026-10-14: 45.5 → 40.5 ms per photo, one worker, cold) are in the Context above.

## Windows measurement (2026-10-14)

Measured by the maintainer on 2026-10-14 with `tests/measure/mh-measure.ps1` (Windows, Docker
Desktop, image built from `main`; runs `measures-20261014-2116` and `-2125`), first audit, fresh cache volume, test folder of photos copied twice:

| Test folder | checks | per file | throughput |
|---|---|---|---|
| 4,000 photos (2.7 GB) | 7.6 s | 1.9 ms | ≈ 350 MB/s |
| 12,000 photos (12.9 GB) | 27.8 s | 2.3 ms | ≈ 465 MB/s |

`fingerprints` 0.0 s (no video in the folder). Only the "after" was measured on Windows: an
image from before 2ea65e4 was not rebuilt (cost judged higher than what it would teach; the
"before" is the devcontainer's 45.5 → 40.5 ms per photo above). Closed on the "after".
