# 0375 — `mh backup` renamed `mh push`: the verb `backup` freed for the index and the settings

- **Priority**: High
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/app.py`, `src/media_hygiene/cli/cmd_backup.py`, `src/media_hygiene/cli/cmd_backup_flow.py`, `src/media_hygiene/cli/cmd_backup_step.py`, `src/media_hygiene/cli/command_actions.py`, `src/media_hygiene/cli/command_functions.py`, `src/media_hygiene/cli/menu_catalog_find.py`, `src/media_hygiene/cli/menu_entry.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/cli/templates/mh_backup.ps1.j2`, `src/media_hygiene/cli/templates/mh_backup.sh.j2`, `src/media_hygiene/actions/kinds.py`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/launcher_backup.py`, `src/media_hygiene/services/launcher_host.py`, `src/media_hygiene/services/backup_place.py`, `src/media_hygiene/services/backup_sources.py`, `src/media_hygiene/services/backup_run.py`, `src/media_hygiene/services/backup_lines.py`, `src/media_hygiene/services/backup_read.py`, `src/media_hygiene/services/backup_journal.py`, `src/media_hygiene/services/backup_broken.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/support/docs/scenario.py`, `tests/measure/mh-measure.ps1`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/backup.md`, `documentation/fr/commands/backup.md`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`

## Why

The maintainer, 2026-10-25: the index and the settings need a save and a restore (0352), and
everybody knows the pair *backup / restore*. `mh backup` is taken by the copy of the photos to
the NAS (0264). That verb becomes `mh push`: one way, only what the target lacks, a photo moved on
the PC renamed there, never sent again, nothing deleted from it at once (like `git push`, which
never deletes on the other side). Its counterpart, `mh pull`, is 0376.

Names set aside (discussed 2026-10-25): `mirror` and `sync` (they promise that deletions follow,
when the verb refuses `robocopy /MIR` and `/PURGE`), `copy` (says nothing of "only what is
missing"), `nas` (a noun, and `folders add --backup` and `import` touch the NAS too).

**No migration**: the maintainer never ran `mh backup` (said 2026-10-25), and is the only user.
No `backup-target.txt`, no `backup` journal exists to read: rename everything, no alias.

## What to do

1. The verb: `mh push [--to <folder>] [--anyway] [--undo <run>]`, `mh.ps1` and `mh.sh` (the bash
   `mh` keeps refusing it, with the PowerShell command). `mh backup` then says nothing special:
   it is 0352's verb; until 0352 lands, an unknown verb.
2. Everything named after the verb, **not** what is named after the *compared backups*
   (`--backup PATH`, `folders add --backup`, `launcher_backups.py`, `backup_reasons`,
   `backup_dealt`, `console/backup_view.py`, `report/backup_views.py`, `_backups.html.j2`: a
   backup as a noun, they stay):
   - templates `mh_backup.*.j2` → `mh_push.*.j2`; `cmd_backup*.py` → `cmd_push*.py`; the
     internal command `backup-step` → `push-step`;
   - the services of the verb (`launcher_backup`, `backup_place`, `backup_sources`, `backup_run`,
     `backup_lines`, `backup_read`, `backup_journal`, `backup_broken`) → `push_*`; read each
     module's docstring first, the list above is from their first line only;
   - `backup-target.txt` → `push-target.txt`; the journal phase `Phase.BACKUP` (`"backup"`) →
     `Phase.PUSH` (`"push"`): to check that no other run writes that phase;
   - the setting `[backup] keep_removed_days` → `[push] keep_removed_days`, its comment; check
     what `config_upgrade` does with a `[backup]` section (none exists on the maintainer's PC
     unless written by default: to check in their `config.toml`);
   - the menu (`backup-to` → `push-to`, its keywords keep `backup nas`: a user searching for
     "backup" still finds it).
3. Documentation en + fr: `commands/backup.md` → `commands/push.md`, one line at the top saying
   it is not `--backup` (a folder compared) nor `mh backup` (0352); `reference-commands.md`, the
   step-3 guide, mkdocs `nav`, `COMMANDS_TOO`; `mh-measure.ps1` (step 21 names the verb).
4. `i18n_update`, the French; `docs_screenshots` to run (said, not run).

## Acceptance

- `mh push --to \\NAS\backup_photos` does what `mh backup --to` did (the unit and integration
  tests of the verb pass under their new names).
- `grep -rn "mh backup" src documentation` finds only 0352's verb (or nothing before 0352).
- `mh push --help` and the page in both languages.

## Gain

A name per job: `push`/`pull` for the photos, `backup`/`restore` for the work of the index
(0352), `import` for a file only a compared backup still holds. No user to migrate: cost of the
rename alone (*estimated*: one session, mostly mechanical).
