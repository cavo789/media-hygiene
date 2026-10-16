# 0187 — CI: a GitHub Release with notes at each `vX.Y.Z` tag; `mh update` links it

- **Priority**: Low
- **Batch**: docker
- **Depends**: —
- **Files**: `.github/workflows/ci.yml`, `documentation/{en,fr}/commands/launcher.md`, `documentation/{en,fr}/reference-troubleshooting.md`

## Why

Follows 0177 (PARTIAL): no release notes exist, so `mh update` and the docs link the Docker Hub
tags page. Decided by the maintainer (inbox, 2026-10-16): CI creates a GitHub Release.

## What to do

- In the publish job of `ci.yml` (tag only, after the image is pushed): `gh release create
  "$TAG" --generate-notes --verify-tag` (permission `contents: write` on that job only; the
  token is the workflow's `GITHUB_TOKEN`). Idempotent on a re-run (`gh release view` first).
- `mh update` and the docs link `https://github.com/cavo789/media-hygiene/releases` instead of
  the tags page (the link lives in `documentation/{en,fr}/commands/launcher.md`).
- Pinned action versions as the rest of the workflow; no new third-party action needed.

## Acceptance

- The commit gate on the workflow; `tests/unit/test_documentation.py` (links).
- The next `release` shows the Release (the maintainer's check, nothing to run here).

## Gain (estimated)

"What changed?" after `mh update`: a list of tags → the notes of each version.
