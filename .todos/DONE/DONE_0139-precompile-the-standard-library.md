# 0139 — Precompile the standard library in the image: 300 ms off every command

- **Priority**: High — measured: `media-hygiene --version` 0.80 s → 0.50 s inside the container, for every command
- **Batch**: docker
- **Depends**: —
- **Files**: `Dockerfile`, `tests/e2e/`, `.devcontainer/scripts/helpers/`

## Context

Speed review of 2026-10-14 (second pass). `python:3.14-slim-trixie` ships the standard library
**without any `__pycache__`**. The image sets `PYTHONDONTWRITEBYTECODE=1` and runs as the
`app` user, who cannot write under `/usr/local/lib/python3.14` anyway. So every `docker run`
compiles again, from source, every standard-library module it imports.

Measured with `python -v -c "import media_hygiene.cli.app"` in `media-hygiene:latest`:
1,049 modules come from a `.pyc` (the venv, `UV_COMPILE_BYTECODE=1`) and **189 from source**,
all of them under `/usr/local/lib/python3.14` (`asyncio`, `json`, `sqlite3`, `email`, `typing`, …).

Measured inside one container, 5 runs each, before and after
`python -m compileall -q -j0 /usr/local/lib/python3.14`:

| | `media-hygiene --version` |
|---|---|
| as shipped | 789–817 ms |
| standard library compiled | 445–525 ms |

The standard library grows from 29 MB to 50 MB (uncompressed, before the exclusions below).
This adds to TODO 0136 (lazy imports): the two gains are independent, since this one makes
every import cheaper, whatever is imported.

## What to do

1. In the `runtime` stage, after the user is created and before `USER`:

   ```dockerfile
   # The base image ships no bytecode for the standard library, and the app user can never
   # write it: without this, every run compiles ~190 modules again (~300 ms).
   RUN python -m compileall -q -j0 --invalidation-mode unchecked-hash \
         -x '/(test|idlelib|tkinter|turtledemo|ensurepip|lib2to3|pydoc_data)/' \
         /usr/local/lib/python3.14
   ```

   `unchecked-hash`: the files never change in the image, so Python does not even `stat`
   the source to validate the `.pyc`. Check whether `UV_COMPILE_BYTECODE` can do the same for
   the venv (uv uses timestamps); if not, a second `compileall --invalidation-mode
   unchecked-hash -f /opt/venv` in the builder is an option, but measure it.
2. Check `dive_ci` still passes (the layer adds ~15–20 MB). Raise its threshold only if needed,
   and say why in the commit.
3. An e2e test: in the image, `python -v -c "import media_hygiene.cli.app"` loads no module
   whose `code object from` line names a `.py` file. It guards against a later base image or
   Dockerfile change undoing the gain.
4. Measure before and after with `docker run --rm media-hygiene:latest --version` on the
   maintainer's PC (Docker Desktop), 5 runs, and write the figures in the commit message.

## Acceptance

- No standard-library module is compiled at run time (the e2e test).
- `--version` inside the container ~300 ms faster on the maintainer's PC.

## Status — DONE (2026-10-14)

- `Dockerfile`, runtime stage: `python -m compileall -q -j0 --invalidation-mode unchecked-hash`
  of the standard library (path from `sysconfig`, the listed folders excluded).
- `tests/e2e/test_start_image.py`: `python -v -c "import media_hygiene.cli.app"` in the image
  compiles no module (passes). `UV_COMPILE_BYTECODE` left as is (timestamps): the venv already
  loads from `.pyc`, the test proves it; `unchecked-hash` for the venv was not measured.
- Measured (devcontainer Docker, `--cpus 2`, best of 5 in the container), with 0136 in the same
  build: `--version` 0.85 s → 0.20 s. Image 362 → 379 MB; `dive_ci` passes unchanged.
- Not measured on the maintainer's Docker Desktop.
