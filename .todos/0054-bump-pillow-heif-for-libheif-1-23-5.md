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
