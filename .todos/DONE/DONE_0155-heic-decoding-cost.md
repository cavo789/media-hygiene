# 0155 — HEIC (iPhone) photos cost ≈ 13× a JPEG to check: measure on real files, then a faster decode

- **Priority**: Medium — an iPhone library of 300,000 photos is ≈ 2 hours of CPU on 16 CPUs (≈ 4 on 8) for the first audit, CPU-bound; the maintainer's own collection has few HEIC files, other users mostly those
- **Batch**: docker
- **Depends**: —
- **Files**: `src/media_hygiene/scan/image_check.py`, `Dockerfile`, `pyproject.toml`


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

## Status — DONE (2026-10-19, was BLOCKED)

### Done (inbox 2026-10-19: the maintainer agreed to public samples)
- Real files: the HEIC of `drewnoakes/metadata-extractor-images` (README: "You are free to use
  these media files however you wish"), downloaded to the session's scratchpad only, never into
  the repository: 6 iPhone tile grids, 12 MP, 48 tiles of 512 px (iPhone 8, XR, 11 Pro ×4;
  0.7–6.2 MB) and one Samsung Galaxy S24 FE grid (33 tiles). No 48 MP file among them.
- Measured in the devcontainer (venv, `inspect_image`, median of 3, `nice -n 19`):
  one process, `DECODE_THREADS` 4 (default) → 107–263 ms wall, 225–698 ms CPU per file;
  `DECODE_THREADS` 1 → 207–635 ms wall, same CPU (216–666 ms). Real grids cost less than the
  synthetic one-frame files above (403–691 ms): ≈ 0.3 s CPU for a typical 12 MP iPhone photo,
  ≈ 10× a JPEG (30.6 ms), not 13×.
- Pool as wide as the CPUs (4 workers pinned to 4 CPUs with `taskset`, 56 files, run twice):
  threads 4 → 11.05 / 10.77 files/s, threads 2 → 11.42 / 10.79, threads 1 → 10.98 / 11.15:
  no difference beyond the noise (±3 %). The oversubscription costs nothing measurable, and the
  threads help when the pool is not full (the last files of a walk). **Decision: keep
  `DECODE_THREADS` at its default** (rejected with these figures).
- Throughput: ≈ 2.75 files/s per CPU (measured on 4) → 300,000 iPhone photos on 16 CPUs
  ≈ 1.9 h of first audit (estimated by scaling; the Priority line's ≈ 2 h stands).
- The image's `ffmpeg` 9.0.2 reads the grid (`ffprobe -show_stream_groups`: one *Tile Grid*
  group of 48 streams) but cannot assemble it: "No such filter: 'xstack'" (measured,
  `media-hygiene:latest`). Using it would need `xstack` in the minimal build, for a decoder
  gain measured at ≈ 1.4× (above, one-frame file), below the 1.5× this TODO sets for a
  follow-up. **No decoder follow-up filed.**

### Not done (dropped)
- libheif built with its FFmpeg decoder plugin: not built; same FFmpeg HEVC decoder, so the
  same ≈ 1.4× (estimated), under the threshold.
- 48 MP files (iPhone 14 Pro and later): none public found with a clear licence; their cost
  per file is ≈ 4× a 12 MP one (estimated from the pixel count), the decision does not change.

### Earlier status — BLOCKED (2026-10-14)

### Not done
- All items remain open.
  **Reason:** the measurement needs a few dozen real iPhone HEIC files (tile grids); the
  maintainer has none (inbox of 2026-10-14). Synthetic HEIC files do not have the tile grids
  that make the cost. Unblocks when someone provides real HEIC files, kept outside the
  repository.
