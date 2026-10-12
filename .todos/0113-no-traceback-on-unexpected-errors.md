# 0113 — An unexpected error never shows a traceback: one calm line, how to report it

- **Priority**: High — a user of the published image saw a full traceback
- **Batch**: safety
- **Depends**: —
- **Files**: `src/media_hygiene/cli/app.py`, `src/media_hygiene/cli/localized.py`, `src/media_hygiene/cli/interrupted.py`, `src/media_hygiene/cli/context.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `.devcontainer/Dockerfile`, `tests/e2e/`, `documentation/en/`, `documentation/fr/`

## Context

2026-10-12, `mh inventory` on the maintainer's photos: an EXIF camera model holding a NUL made
openpyxl raise `IllegalCharacterError` (fixed since, in `text_safe_cell` and `exif_values.text`).
The user saw Typer's Rich traceback, 15 frames down to openpyxl. `user_errors` (`cli/context.py`)
only turns `MediaHygieneError` into a message with a tip; any other exception reaches Typer,
whose `pretty_exceptions_enable` is on by default. The maintainer's rule: an ordinary user of the
image never sees a stack trace; debug aids stay in dev tooling or an explicit opt-in.

Ctrl+C already has its safety net: `LocalizedGroup.invoke` (`cli/localized.py`) catches
`KeyboardInterrupt` and calls `stop_on_interrupt`, which says whether the photos were left
untouched (`READ_ONLY_COMMANDS`). An unexpected error deserves the same treatment.

## Goal

- `typer.Typer(..., pretty_exceptions_enable=False)` in `build_app`.
- `LocalizedGroup.invoke` also catches `Exception` (not `typer.Exit`, `click` usage errors,
  `SystemExit`, nor `KeyboardInterrupt`, already handled) and prints, through `Output`:
  - one error line: what failed, in plain words, with the exception type and message (escaped,
    no markup), e.g. `Unexpected error during inventory: IllegalCharacterError: …`;
  - the reassurance line `stop_on_interrupt` already gives: read-only command → photos untouched;
    `clean`/`undo`/`sort`… → the journal holds what was done, `undo` line;
  - a 💡 tip: how to report it (the GitHub issues URL, the version, the command typed), and that
    `MEDIA_HYGIENE_DEBUG=1` shows the details;
  - exit with `ExitCode.FAILURE`.
- `MEDIA_HYGIENE_DEBUG=1` (opt-in, never set in the image `ENV`) re-raises, so the developer
  gets the full traceback; the devcontainer may set it for `hygiene` runs.
- Share the reassurance wording with `interrupted.py` rather than copying it (≤ 200 lines/file).
- Every new string through `_()`, `i18n_update`, French translated.
- Docs: a line in the troubleshooting / FAQ page of both languages (what to send when it happens).

## Acceptance

- A unit test injects a command raising `RuntimeError`: output has no `Traceback`, no file path
  of the venv, holds the error line and the tip; exit code is `FAILURE`.
- Same test with `MEDIA_HYGIENE_DEBUG=1`: the exception propagates.
- `typer.Exit`, usage errors (`--bad-option`) and Ctrl+C behave as before (existing tests pass).
- An e2e case on the image: an unexpected error prints no traceback.
