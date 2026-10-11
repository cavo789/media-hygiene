# 0054 — Bump `pillow-heif` to 1.9.0 once released: libheif 1.23.5 security fixes

- **Priority**: Medium — libheif parses every HEIC file of the collection; one fix is rated high
- **Batch**: dependencies
- **Depends**: —
- **Files**: `pyproject.toml`, `uv.lock`

## Context

The image ships `pillow-heif` 1.8.0 (libheif 1.23.4, libde265 1.1.3). libheif 1.23.5
(2026-09-21) fixes, among others, GHSA-v8qw-hwjv-44hw (high): a crafted HEIC/AVIF declaring a
small `ispe` but a huge coded frame makes the decoder allocate hundreds of MB to more than 10 GB
before libheif rejects it. That is exactly what an audit does to every HEIC file it meets: one
such file could exhaust the memory of a scan worker. The other fixes of 1.23.5 are medium/low
(JPEG 2000 palette amplification, unci alpha compositing out-of-bounds read, ...).

`pillow-heif` bumped its bundled libheif to 1.23.5 on its main branch on 2026-09-23 (#491,
changelog section "1.9.0 - unreleased"), but 1.9.0 was not on PyPI on 2026-10-02 (found while
processing TODO 0045).

## Proposal

- When `pillow-heif` 1.9.0 (or later) is on PyPI with cp314 manylinux wheels for x86_64 **and**
  aarch64: `pillow-heif>=1.9.0` in `pyproject.toml`, `uv lock`.
- Check its changelog for API changes touching `register_heif_opener()` (the only call the tool
  makes, `scan/image_check.py`) and `from_pillow(...).save(...)` (the tests and
  `tests/support/docs/shots.py`).
- `build`, then `docker run --rm --entrypoint python media-hygiene:latest -c "import
  pillow_heif; print(pillow_heif.libheif_info())"` shows libheif 1.23.5 or later; `e2e`.

## Acceptance

- [ ] `uv.lock` pins `pillow-heif` ≥ 1.9.0; the image reports libheif ≥ 1.23.5.
- [ ] Unit, integration and e2e tests green (HEIC metadata in `test_image_metadata.py` included).

## Status — PARTIAL (2026-10-11)

### Done
- `pillow-heif` 1.9.0 is not on PyPI, but 1.8.1 is (2026-10-11): its changelog says libheif
  1.23.4 → **1.23.6** (#491 #499, so the 1.23.5 fixes are in), libx265 4.2 → 4.3, and
  "saving `;10`/`;12` data with sample values above its bit depth now raises `ValueError`" (no
  API change for `register_heif_opener()` nor `from_pillow(...).save(...)`). cp314 manylinux
  wheels exist for x86_64 and aarch64.
- `pyproject.toml`: `pillow-heif>=1.8.1`; `uv lock --upgrade-package pillow-heif` (only that
  package moved). In the devcontainer `pillow_heif.libheif_info()` reports libheif 1.23.6.
- Unit and integration tests touching HEIC/HEIF: 65 passed; the full suite runs at the end of
  the lot.

### Not done
- `build`, the `libheif_info()` check inside `media-hygiene:latest`, and `e2e`.
  **Reason:** no Docker build nor e2e during the night run (machine load); the maintainer runs
  them before pushing.
- Note for later: `pillow-heif` 1.9.0 will require Pillow 13 (Python ≥ 3.11, fine here): bump
  both together when it is out, as an ordinary dependency update (`deps`).
