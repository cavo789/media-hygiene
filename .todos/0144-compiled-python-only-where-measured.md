# 0144 — Compiled Python (mypyc, Cython, Nuitka): only where 0131 shows Python-bound time

- **Priority**: Low — revisit only if the `near duplicates` stage of `Time per step` passes ~10 s on a warm audit (2026-10-14: 1.5 s for 52,056 files); try numpy, or skipping the second `find_similar` run, before any compilation
- **Batch**: decision
- **Depends**: —
- **Files**: `src/media_hygiene/plan/near.py`, `src/media_hygiene/plan/bursts.py`, `src/media_hygiene/plan/near_video.py`, `src/media_hygiene/scan/visual.py`, `Dockerfile`, `pyproject.toml`

## Context

Speed review of 2026-10-14 (second pass). The maintainer asked whether Python compiled at image
build time would help. Where the time goes today:

| Work | Runs in |
|---|---|
| SHA-256 (`scan/hashing.py`) | OpenSSL (C, SHA-NI), GIL released, disk-bound |
| Image decode | Pillow + libjpeg-turbo 3.1, libheif, LibRaw (C), in a process pool |
| Hashes, sharpness, colour | numpy (C) on small arrays |
| Videos | `ffprobe` / `ffmpeg` (C) |
| Index | `sqlite3` (C); the per-row pydantic parse is pydantic-core (Rust), see 0135 |
| Start-up | imports: see 0136 (lazy) and 0139 (bytecode of the standard library) |

Bytecode is already precompiled for the venv (`UV_COMPILE_BYTECODE=1`). What is left in pure
Python is loops over files: candidate pairs in `near._clusters` (`combinations` inside each
16-bit quarter bucket), bursts, keep policy, report building.

- **mypyc**: the code base is mypy-strict, so it is the best-suited compiler. Typical gain is
  2–4× on pure-Python loops, but it compiles whole modules: pydantic models, `dataclass`
  `slots`, `@override`, generics with PEP 695 syntax and `TYPE_CHECKING` imports all need
  checking. It also means a native wheel per platform, built in the `builder` stage.
- **Cython**: would mean rewriting modules in another dialect. No.
- **Nuitka** (whole program): it would not speed up the imports, whose cost is building pydantic
  and dataclass objects at import time, not running bytecode. It would also break the
  uv/venv layout and the `--help` captures tooling. No.

## What to do

1. Wait for the 0131 step timings of a warm and a first audit on the real collection.
2. If a pure-Python step (similar search, bursts, keep policy) takes more than a few seconds,
   **vectorise it with numpy first**. Example for `near._clusters`: within a bucket, compare
   all hashes at once with `np.bitwise_count(phashes[:, None] ^ phashes[None, :])` (numpy ≥
   2.0, already a dependency), instead of `combinations` + `int.bit_count`. Same results,
   checked by the existing unit tests.
3. Only if a step is still Python-bound after that, try `mypyc` on that single module (e.g.
   `plan/near.py` + `plan/likeness.py`), built in the `builder` stage, with the pure-Python
   module as fallback for the devcontainer and tests. Keep it only if it measures faster on
   the real collection.
4. Otherwise close this TODO as UNNEEDED with the figures.

## Acceptance

- A written answer, with figures: which steps (if any) were Python-bound, what was done, the
  times before and after.
