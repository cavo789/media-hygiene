# 0519 — Upkeep routine: one click runs the regular chores, like `[imports]`

- **Priority**: Medium
- **Batch**: home
- **Depends**: 0514
- **Files**: `src/media_hygiene/config/templates/`, `src/media_hygiene/config/import_settings.py`, `src/media_hygiene/services/import_run.py`, `src/media_hygiene/cli/menu_catalog_clean.py`, `src/media_hygiene/review/home_parts.py`, `documentation/en/commands/`, `documentation/fr/commands/`

## Asked (maintainer, 2026-10-30)

The `[imports]` chain ("everything is done after an import") was a success; generalise it.

## What

- A `[routine]` list in `config.toml`, same shape as `[imports]`: steps in order, remove one to
  switch it off. Proposed steps: `audit` (incremental), `copies` (exact copies to the quarantine,
  `mh undo` puts them back), `purge` (quarantine runs older than N days, the confirmation of
  `purge` kept), `reports` (refresh).
- One "Upkeep" action on the home page and in the menu (`menu_catalog_*`), followed in the page
  (0514), ending on one 👉 What next line: the page that still has work (bursts, near, intruders).
- Reuse the step runner of the import chain rather than a second one.
- N days: a named constant first (few settings rule); say in the report whether it should become
  a setting.

## Done when

One click on the home page runs the steps listed, a step removed from the list is skipped
(test), and the docs (both languages) describe `[routine]`.
