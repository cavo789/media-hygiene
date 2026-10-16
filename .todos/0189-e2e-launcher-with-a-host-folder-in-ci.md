# 0189 — e2e in CI: `launcher --photos` on a real host folder, `mh folders add`, then `mh audit`

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `tests/e2e/test_launcher_image.py`, `tests/e2e/conftest.py`, `.github/workflows/ci.yml`

## Why

Follows 0173 and 0176 (PARTIAL): the e2e tests use the demo tree in a named volume, and Docker
cannot bind-mount a host folder from inside the devcontainer's volume, so `launcher --photos`
and "`mh folders add`, then audit it" are only tested by text here. A GitHub runner has a real
host filesystem. Decided by the maintainer (inbox, 2026-10-16).

## What to do

- An e2e test (marker `e2e`, plus a marker or skip condition "host folders available": an env
  var CI sets, e.g. `MEDIA_HYGIENE_E2E_HOST_DIR`) that copies a few demo files into a runner
  temp folder, runs `launcher --photos <it>` into `mh.sh`, sources it, `mh audit` (exit 0, the
  copies found), then `mh folders add <second folder>` and `mh audit` again (both folders seen).
- Skipped in the devcontainer (no such variable), with the reason.
- CI: set the variable in the e2e job.

## Acceptance

- Green in CI on the pull request; skipped locally with its reason.

## Gain (estimated)

The launcher's folder handling: tested as text only → run for real at each push.
