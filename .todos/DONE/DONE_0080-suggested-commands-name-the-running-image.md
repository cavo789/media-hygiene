# 0080 — Suggested commands name the image that is running, not always the published one

- **Priority**: Low — only developers run another image than `cavo789/media-hygiene`
- **Batch**: guidance
- **Depends**: —
- **Files**: `src/media_hygiene/paths/docker_run.py`, `src/media_hygiene/services/next_command.py`, `src/media_hygiene/services/launcher.py`, `.devcontainer/scripts/helpers/*.sh`, `tests/unit/test_next_command.py`

## Context

`DockerRun.render()` always writes `PUBLISHED_IMAGE` (`cavo789/media-hygiene`) in the commands
the tool suggests (👉 next step, safety lines, the missing-mount error of `places`). A run of the
locally built `media-hygiene` image therefore suggests the published image, which may be older:
pasting it gave `Invalid configuration (general.timezone: Extra inputs are not permitted)`
because v0.3.0 predates `[general] timezone`, written by the local build's own advice.

A container cannot learn the name it was started under (not in `/proc`, not in the mount table).

## What to do

- Read an optional `MEDIA_HYGIENE_IMAGE` variable (constant next to `PUBLISHED_IMAGE`); default
  the published name. Keep it out of `environment()` carry-over (it is passed explicitly), or
  carry it, so the suggested command keeps naming the same image.
- Set it in the local image build (`ENV` in a dev/local target, or `--build-arg`) or in the
  `build` / `e2e` / `docs_screenshots` helpers, so that `docker run media-hygiene …` suggests
  `media-hygiene`. Check that the published image never sets it.
- The `launcher` script uses the same name (TODO 0075 swaps it by hand today).

## Acceptance

- With `MEDIA_HYGIENE_IMAGE=media-hygiene`, `next_command` renders `media-hygiene <verb>`;
  without it, `cavo789/media-hygiene <verb>` (unit tests).
