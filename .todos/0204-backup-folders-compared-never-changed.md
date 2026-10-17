# 0204 — A backup or an old disk: compared, never changed — what is missing on either side

- **Priority**: High — the two questions families ask: "can I wipe this old disk?", "is my backup complete?"
- **Batch**: keep-policy
- **Depends**: —
- **Files**: `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/cli/options.py`, `src/media_hygiene/cli/cmd_audit.py`, `src/media_hygiene/cli/cmd_clean.py`, `src/media_hygiene/cli/cmd_review.py`, `src/media_hygiene/cli/cmd_crosscheck.py`, `src/media_hygiene/plan/planner.py`, `src/media_hygiene/plan/backups.py` (new), `src/media_hygiene/services/audit.py`, `src/media_hygiene/crosscheck/czkawka.py`, `src/media_hygiene/report/backup_views.py` (new), `src/media_hygiene/report/templates/_backups.html.j2` (new), `src/media_hygiene/report/templates/report.html.j2`, `src/media_hygiene/console/backup_view.py` (new), `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_backups.py` (new), `tests/integration/test_backup_audit.py` (new), `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`, `documentation/en/clean/05-choose-the-kept-copy.md`, `documentation/fr/clean/05-choose-the-kept-copy.md`, `documentation/en/clean/07-configuration-file.md`, `documentation/fr/clean/07-configuration-file.md`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`, `documentation/en/reference-glossary.md`, `documentation/fr/reference-glossary.md`, `documentation/en/reference-troubleshooting.md`, `documentation/fr/reference-troubleshooting.md`, `documentation/en/commands/audit.md`, `documentation/fr/commands/audit.md`

## Context

Chosen by the maintainer on 2026-10-17 (proposal F2). Today a real backup must be excluded
(`--exclude`, `[folders] excluded`): never read, so the tool cannot say whether it is complete. An
old disk can be cleaned against the library, but not checked before wiping it. Competitors (vendor
pages, 2026-10-17): Duplicate Cleaner Pro searches "unique files" and has "master folders";
Duplicate Photo Cleaner has a folder comparison "to merge folders and manage backups".

## Design (proposed 2026-10-17)

- A fourth folder role, **backup**: `--backup PATH` (audit, review, clean, crosscheck), and
  `[folders] backups = [...]`. A backup folder is read and compared, never changed (like a
  protected one), and never the reason a copy elsewhere goes (unlike a protected one): its files
  are left out of the duplicate groups, the near duplicates and the burst series.
- Compared by content with the existing exact pipeline (a file whose size no other file has has no
  copy; the others get their SHA-256). A resized or recompressed copy does not count as backed up.
- Two results per backup folder, counts and sizes: (1) the library's files without an identical
  copy in it ("not in the backup"); (2) its files without an identical copy in the library ("only
  in the backup": deleted from the library, or to copy before wiping an old disk). The console
  says both in two lines; the report lists them, host paths, with two CSV files next to
  `plan.csv` (`backup-missing.csv`, `backup-only.csv`).
- The old disk is the same role: mark it `--backup`, read (2): "these 37 files are nowhere else:
  copy them first".
- A folder cannot be both backup and preferred, protected or excluded, nor lie inside one of
  them (or contain one): refused, naming both, as the config validators do.
- `crosscheck`: the backup folders are left out of Czkawka's run as well (its groups would mix
  them).
- Size caps: `cli/cmd_audit.py` is full (200/200) and `services/audit.py` near it (182/200): make
  room in `cmd_audit.py` first (move a block to a helper module, as the other commands do) before
  adding `--backup`; the coverage step lives in `plan/backups.py`, the audit service only calls it.

## Explicit non-goals

- No copy: the tool says what to copy, the user copies.
- `excluded` keeps its meaning (never read).
- `mh` mounting a backup read-only for every command, `clean` included: 0205.

## Acceptance

- Unit and integration: a library and a backup holding identical files, a file only in the
  library, a file only in the backup, a resized copy (counts as missing), a backup file identical
  to two library files; `clean` never touches a backup file and never removes a library file
  because of a backup copy; overlapping roles refused.
- Console, report and the CSV files say both results, in both languages.
- Docs both languages: step 3's "A real backup? Leave it out" becomes "Compare it" (`--backup`),
  the options table, the glossary, the configuration page, the troubleshooting entry "A real
  backup is seen as duplicates". Say in the report that `docs_screenshots` should run.
- Time: the first audit of a backup reads it like any folder (its candidates hashed); say it in
  the docs with the measured throughput of a first audit (0160: ≈ 465 MB/s on the maintainer's
  PC).

## Gain (estimated)

"Can I wipe this disk?" goes from impossible in the tool (an excluded folder is never read) to one
audit listing the files to copy first; for a backup, the list of what it lacks.
