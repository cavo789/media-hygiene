# 0740 — What 0505 left: Home page: run the short container steps in the page, their output in a popup

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `.todos/DONE/0505-home-run-container-steps-in-a-popup.md`, `src/media_hygiene/cli/menu_entry.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/home_texts.py`, `src/media_hygiene/services/home_pages.py`, `src/media_hygiene/review/shared_routes.py`, `documentation/en/commands/home.md`

Split from section 0505 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0505-home-run-container-steps-in-a-popup.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- `people --forget` and `restore` (they prompt: need a "yes" flag skipping the console
- `backup` names the zip it wrote (its own output); not re-read from disk by the page.

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-13)

### Done
- `backup` names its zip: already done — `make_backup` reads the archive back (a
  `BackupError` when it does not read back whole) and the command says *Backup written and
  read back: <path> (<size>)*, which the page's dialog shows. Nothing to change.
- `people --forget` runs in the page (`inline=True`, `menu_catalog_settings.py`): the faces
  are deleted and read back from the index in the dialog. Its question about the names of
  `config.toml` gets no answer (no terminal: stdin is closed), so the names stay and the
  output says to answer yes in a terminal — the safe default, no new flag. Tests
  `test_inline_step.py`, `test_menu_catalog.py` (`STILL_IN_THE_WINDOW` shrinks by one). Docs
  EN + FR (`commands/home.md`).

### Not done
- `restore` in the page. It asks nothing (no prompt, contrary to the 0505 note), but it
  replaces the index file while the home server, in the same container, may hold it open
  (its state, the audit of the page); today it runs once the server is stopped.
  **Reason:** needs a decision (stop the page's index readers during the swap, or keep it in
  the window) and a test of the swap under a running server.
- Deleting the names of `config.toml` from the page (a confirmation in the page, then a
  `--names` flag). **Reason:** a new CLI option for a privacy action: the maintainer decides.
- `docs_screenshots` should run (the home page doc changed).
