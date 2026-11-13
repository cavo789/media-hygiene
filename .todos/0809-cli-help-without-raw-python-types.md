# 0809 — CLI help without raw Python types (`<bool>`, `<list[str]>`)

- **Priority**: High
- **Batch**: cli
- **Depends**: —
- **Files**: `src/media_hygiene/cli/app.py`, `src/media_hygiene/cli/`, `tests/unit/`, `documentation/en/commands/`, `documentation/fr/commands/`

## Context

Since the lock file maintenance (commit 908ed73e, `typer` 0.27.3 → 0.29.0), every
`--help` prints a raw Python type before each option's help (`--help -h <bool>`,
`--prefer <list[str]>`), which takes up to 14 columns of an 80-column console and wraps
the help texts (*measured* 2026-11-13: `COLUMNS=80 python -m media_hygiene audit --help`).
A user of Windows PowerShell does not read `list[str]`. The captures of the
documentation were regenerated with it (commit "Docs: captures regenerated", 132 files).

## Proposal

- Find the Typer 0.29 setting or the metavar per option that brings back the 0.27 look
  (no type for a flag; a word the user understands, e.g. `FOLDER`, for a value), set once
  in `cli/app.py` or the shared option helpers, never option by option if avoidable;
  metavars through `_()` with their French.
- A test: no `--help` of any command contains `<bool>`, `list[`, `<str>`, `<int>`.
- Then say that `docs_screenshots` should run (never run it unasked).

## Acceptance

- [ ] `mh audit --help` at 80 columns: no raw type, help texts on one line as before
- [ ] The test above over every command
- [ ] French metavars, if any
