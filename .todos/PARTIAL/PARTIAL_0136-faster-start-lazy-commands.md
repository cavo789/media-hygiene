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

## Status — PARTIAL (2026-10-14)

### Done
- Every `cli/cmd_*.py` keeps at module level only what Typer reads (signatures, option
  types, help texts) and imports the rest inside the functions that use it (moved by an AST
  script, then checked by hand). Ruff `PLC0415` is ignored for `cli/cmd_*.py` in
  `pyproject.toml`, with the reason; pylint gets a module-level
  `import-outside-toplevel` (and `too-many-locals` where the imports push a command past 15
  locals, imports counting as locals).
- Heavy imports on the path every command takes, found with `-X importtime`:
  - `config.classify_places` → `geo.areas` / `geo.distance` (numpy): the numpy-free shape
    checks moved to `geo/shapes.py`, `Point` to `geo/point.py` (both re-exported);
  - `config.people_settings` → `faces.cluster` (numpy) for one constant: `faces/similarity.py`;
  - `services.runtime` → `scan.image_check` (Pillow): imported when the first pool is made;
  - `config.loader` → `i18n.templates` (Jinja2): imported when the default file is rendered.
- Measured in the devcontainer (best of 9): `python -m media_hygiene --version` **0.49 s →
  0.20 s**, `status --help` the same; `media_hygiene` modules loaded for `--version`: 502 → 125.
  The `--help` of the root and of every command is byte for byte the same as before.
- `tests/unit/test_start_imports.py`: `--version`, `--help`, `status --help` load none of
  numpy, openpyxl, Pillow, Jinja2, rawpy, OpenCV. Tests that patched a name in a `cmd_*`
  module now patch it where it is defined.

### Not done
- The measure in the image (`docker run --rm media-hygiene:latest --version`, target under
  0.7 s). **Reason:** it needs an image build, kept for the maintainer (low machine load).
