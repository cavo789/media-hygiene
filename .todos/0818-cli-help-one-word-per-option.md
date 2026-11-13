# 0818 — CLI help: one word per option for its value (`--prefer FOLDER`)

- **Priority**: Low
- **Batch**: cli
- **Depends**: —
- **Files**: `src/media_hygiene/cli/help_types.py`, `src/media_hygiene/cli/`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_cli_help_types.py`

Follows 0809 (commit f1c9f583: values named by generic words, `TEXT`, `NUMBER`, `PATH`).
Decided by the maintainer in the review of 2026-11-13 (`feedback-2026-11-13-3-iterate`): one
word per option, so the help says what to type.

## Proposal

- A `metavar=_("FOLDER")` (or a shared word from a small module of metavars: `FOLDER`, `DRIVE`,
  `FILE`, `NAME`, `DATE`, `COUNT`, `PORT`, `MODEL`…) on each option taking a value, about 60
  options; the same word for the same kind of value everywhere; French words through `_()`
  (`DOSSIER`, `LECTEUR`, `FICHIER`, `NOM`, `DATE`, `NOMBRE`, `PORT`, `MODÈLE`).
- `help_types.PlainTypes` stays as the fallback for an option without a metavar.
- A test: every option taking a value has its own metavar (none falls back to the generic word).

## Acceptance

- [ ] `mh audit --help` shows `--prefer FOLDER`, `--protect FOLDER`; French help shows `DOSSIER`
- [ ] The test above over every command
- [ ] Say that `docs_screenshots` should run
