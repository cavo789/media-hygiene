# 0096 — Run `e2e` on the image with `pillow-heif` 1.8.1 (libheif 1.23.6)

- **Priority**: Medium — check before the next push to `main` (a push rebuilds the published image)
- **Batch**: docker
- **Depends**: —
- **Files**: `tests/e2e/`, `pyproject.toml`, `uv.lock`

## Context

TODO 0054 moved `pillow-heif` from 1.8.0 to 1.8.1 (commit 71e7d58), for libheif 1.23.6, which
holds the 1.23.5 security fixes. Already checked (2026-10-12): the image built by
`docs_screenshots` reports `pillow-heif 1.8.1`, `libheif 1.23.6`, `libde265 1.1.3`, and the
documentation demo (HEIC photos included) ran through it. The end-to-end tests did not run with
this version yet.

## Goal

- `e2e` (builds `media-hygiene:latest`, then `pytest -m e2e`; log in `/tmp/media-hygiene/e2e.log`),
  alone on the machine (heavy step).
- Every test passes, the HEIC ones included. A failure linked to the new version: say which,
  decide between fixing and going back to 1.8.0 (revert 71e7d58).

## Acceptance

- `e2e` green with `pillow-heif` 1.8.1; result written in this TODO's status.
