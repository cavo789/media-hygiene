# 0117 — Import `pillow_heif` and `rawpy` only where pictures are decoded

- **Priority**: Medium — a lead on the rare silent crash (0053), and a faster start of every command
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/scan/image_check.py`, `src/media_hygiene/scan/raw_check.py`, `tests/unit/`

## Context

PARTIAL 0053: one e2e run in four saw `undo` after `clean` exit 139 (segfault) with no output.
Today `image_check.py` imports `pillow_heif` (libheif, libde265, x265) and `raw_check.py`
imports `rawpy` (LibRaw) at module level, so commands that never decode a picture (`undo`,
`history`, `purge`, `config`, `reports`, `launcher`…) may still load these native libraries,
depending on the import graph. Decided in review 0056 (2026-10-12): import them lazily. The
maintainer's PC crashes only with this project (not under other Docker loads), so the code
lead stays open.

## What to do

1. Measure first: `python -X importtime -m media_hygiene undo --help` (and `history`) — which
   commands load `pillow_heif` / `rawpy` today, and how long the import takes.
2. Move the imports inside the functions that decode (`pillow_heif.register_heif_opener()`
   once, guarded, in the worker that opens images; `rawpy` inside the RAW functions). Keep the
   types for mypy through `TYPE_CHECKING` where needed (`rawpy._rawpy` names).
3. Process pool workers: the HEIF opener must still be registered in each worker before the
   first decode (check the pool initialiser, if any).
4. A unit test: importing `media_hygiene.cli.app` and building the app leaves `pillow_heif` and
   `rawpy` out of `sys.modules`.
5. Note the before/after start-up time of `undo --help` in the closing status.

## Explicit NON-goals

- Fixing 0053 itself: if a crash shows again, its `/tmp/media-hygiene/e2e.log` goes to Claude.
- Replacing `pillow-heif` (0045 decided to keep it).

## Acceptance

- `undo`, `history`, `purge`, `config` never load `pillow_heif` nor `rawpy` (test).
- Audits still decode HEIC and RAW files (existing integration tests pass).
