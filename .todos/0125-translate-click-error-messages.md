# 0125 — Command-line errors in French too ("Error", "No such option", "Try … for help")

- **Priority**: Low
- **Batch**: guidance
- **Depends**: —
- **Files**: `src/media_hygiene/cli/localized.py`, `src/media_hygiene/cli/app.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/`

## Context

Review 0056 (2026-10-12), `mh classify --path "C:\Photos\2015"` under `--locale fr`:

```text
Utilisation : media-hygiene classify [OPTIONS]
Try 'media-hygiene classify -h' for help.
╭─ Error ──────────────────────────────────────╮
│ No such option: --path                       │
```

`localized.py` already translates "Usage:"; the rest of Click's/Typer's error output stays in
English (Typer vendors Click without its gettext calls). Half-French errors are exactly what a
beginner meets first.

## What to do

- Translate the error panel title, the "Try '…' for help." hint and the common usage errors
  (`No such option`, `Missing argument`, `Invalid value`, `Got unexpected extra argument`, and
  Click's "Did you mean" suggestions) the way `localized.py` does for "Usage:" — by overriding
  the formatting hook or catching `click.UsageError` and rendering its parts through `_()`.
- When the unknown option exists on a sibling command (here `--path`, known by `tags` and
  `people`), a one-line hint is welcome but optional.

## Explicit NON-goals

- Adding `--path` to `classify` (not decided; `--year` is its scope option).

## Acceptance

- Under `--locale fr`, an unknown option prints no English word (test with Typer's runner).
