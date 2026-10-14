# 0155 — HEIC (iPhone) photos cost ≈ 13× a JPEG to check: measure on real files, then a faster decode

- **Priority**: Medium — an iPhone library of 300,000 photos is ≈ 2 hours of CPU on 16 CPUs (≈ 4 on 8) for the first audit, CPU-bound; the maintainer's own collection has few HEIC files, other users mostly those
- **Batch**: docker
- **Depends**: —
- **Files**: `src/media_hygiene/scan/image_check.py`, `Dockerfile`, `pyproject.toml`
- **Needs maintainer**: a few dozen real iPhone HEIC files (tile grids), kept outside the repository

## Context

Speed and cache review of 2026-10-14 (third pass). The maintainer asked whether binaries (Rust
or other) could speed up the slow parts. For JPEG, no: libjpeg-turbo decodes at a reduced scale
(`draft`), SHA-256 is OpenSSL with SHA-NI, and a first audit on Windows waits for the disk
(0148). HEIC is the exception: HEVC has no reduced decode, every tile is decoded in full.

Measured on 2026-10-14 in the devcontainer, 12 MP pictures made from the same synthetic photo
(`pillow-heif`'s encoder: one frame, not the tile grid of an iPhone), one process:

| | `inspect_image` (audit check) | of which decode |
|---|---|---|
| JPEG, 3.4 MB | 30.6 ms | 21.6 ms (drafted) |
| HEIC, 2.2 MB | 403 ms | 325 ms |
| HEIC, 8.0 MB | 691 ms | 626 ms |

- libheif's threads (`pillow_heif.options.DECODE_THREADS`, 4 by default) change nothing on
  these one-frame files. A real iPhone HEIC is a grid of 512 × 512 tiles that libheif decodes on
  4 threads, in each of the pool's processes (one per CPU): up to 4 times more threads than
  CPUs, not measured.
- FFmpeg's HEVC decoder, the image's own `ffmpeg` 9.0.2 on the 2.2 MB file (`-threads 1`,
  demuxing included): 0.23 s of CPU, against 0.33 s for libheif with libde265: ≈ 1.4×. FFmpeg
  reads the HEIF file directly (one `hevc` stream for a one-frame file).
- Rust brings nothing here: there is no production HEVC decoder in Rust; the bindings
  (`libheif-rs`) wrap the same libheif.

## What to do

1. Get real HEIC files: a few dozen from an iPhone (tile grids, 12 and 48 MP), or public
   samples with a licence that allows it, kept outside the repository.
2. Measure on them, per file (wall and CPU) and as the throughput of a pool of one process per
   CPU:
   - today's settings;
   - `DECODE_THREADS = 1` in `prepare_image_worker` (no oversubscription);
   - the image's `ffmpeg` decoding the grid (FFmpeg reads HEIF tile grids since 7.1; check that
     our minimal build assembles them, which may need a filter it lacks);
   - libheif built with its FFmpeg decoder plugin (libheif ≥ 1.17), in a throwaway build
     stage: build time for amd64 and arm64, image size, licences.
3. Do item 2's `DECODE_THREADS` change if it helps (one line). File a follow-up for a decoder
   change only if it is ≥ 1.5× faster on the real files: the check must still decode every tile
   (the integrity rule), and the visual facts must stay identical, or `METADATA_VERSION` /
   the visual version must change (every HEIC decoded again once).

## Acceptance

- The figures of item 2 written here; the `DECODE_THREADS` decision applied or rejected with its
  figures; a follow-up TODO for the decoder if it qualifies.

## Status — BLOCKED (2026-10-14)

### Not done
- All items remain open.
  **Reason:** the measurement needs a few dozen real iPhone HEIC files (tile grids); the
  maintainer has none (inbox of 2026-10-14). Synthetic HEIC files do not have the tile grids
  that make the cost. Unblocks when someone provides real HEIC files, kept outside the
  repository.
