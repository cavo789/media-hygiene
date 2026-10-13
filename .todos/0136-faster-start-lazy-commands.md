# 0136 — Start faster: import a command's code only when that command runs

- **Priority**: Medium — about 0.8 s of the ~1.1 s that each `docker run` takes before doing anything
- **Batch**: cli
- **Depends**: —
- **Files**: `src/media_hygiene/cli/command_table.py`, `src/media_hygiene/cli/commands.py`, `src/media_hygiene/cli/app.py`, `src/media_hygiene/cli/cmd_*.py`, `src/media_hygiene/__main__.py`, `pyproject.toml`

## Context

Speed review of 2026-10-14, measured:

| | time |
|---|---|
| `docker run --rm --entrypoint python media-hygiene:latest -c pass` | 0.34 s |
| `docker run --rm media-hygiene:latest --version` | 1.1–1.3 s |
| devcontainer `python -m media_hygiene --version` | 0.5 s, of which 0.44 s imports |

`python -X importtime` shows that `cli/command_table.py` imports every `cmd_*` module, and with
them every service. For `--version`, `status` or `--help`, this loads:

- `cli.audit_people` → `cli.people_flow` → `faces.cluster` → **numpy**: 134 ms;
- `classify.workbook.writer` → **openpyxl**: 32 ms;
- `crosscheck.czkawka`: 41 ms;
- `rich.markdown`, `asyncio` and 487 `media_hygiene` modules: 196 ms in total, mostly pydantic
  models and dataclasses built at import.

The image already precompiles the bytecode (`UV_COMPILE_BYTECODE=1`), so this cost is the imports
themselves. Every command pays it: `status`, `history` and `--help` included.

## What to do

1. Measure in the image: `docker run --rm --entrypoint python media-hygiene:latest -X importtime
   -m media_hygiene --version`.
2. Keep in `cmd_*.py` only what Typer needs to build the command (the signature, the option types,
   the help texts). Move the body into the module that does the work, and import that module
   inside the command function.
   Trade-off to accept: ruff `PLC0415` (import-outside-toplevel) needs a per-file ignore for
   `cli/cmd_*.py`, documented in `pyproject.toml` next to the existing Typer exception. The
   alternative, a small `lazy(module, name)` helper using `importlib`, hides the import from mypy.
   Prefer the plain local import.
3. Look for numpy, openpyxl, PIL and jinja2 imported at module level by modules that only need
   them in one function, e.g. `faces.cluster`.
4. Add a test that `media_hygiene --version` does not import `numpy`, `openpyxl` or `PIL`: run a
   subprocess and check `sys.modules`. It guards the gain.

## Acceptance

- `docker run --rm media-hygiene:latest --version` under 0.7 s on the maintainer's PC, measured
  before and after.
- No change in the help output, the commands or their options (the `--help` captures of the docs
  stay identical).
