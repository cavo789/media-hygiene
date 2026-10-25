# 0352 — `mh backup` / `mh restore`: the index and the settings kept outside Docker's cache volume

- **Priority**: High
- **Batch**: launcher
- **Depends**: 0375
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/cli/templates/mh_backup.ps1.j2`, `src/media_hygiene/cli/templates/mh_backup.sh.j2`, `src/media_hygiene/cli/cmd_backup.py`, `src/media_hygiene/services/cache_backup.py`, `src/media_hygiene/services/cache_restore.py`, `src/media_hygiene/services/launcher_kept.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/backup.md`, `documentation/fr/commands/backup.md`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`

## Context

Asked by the maintainer (2026-10-24): `/cache` is the named Docker volume `media-hygiene-cache`
(`services/launcher_kept.py`, `CACHE_VOLUME`). It is the only tool folder that is not in
`$HOME\media-hygiene\` (`config`, `journal`, `quarantine`, `reports`, `mh.ps1`, `nas-*.xml` are
there already). A `docker volume prune`, a reset of Docker Desktop or a reinstalled WSL erases it.
The index now holds work that is long to redo: besides digests, visual facts, metadata and video
fingerprints, the tables `tags`, `descriptions`, `meanings` and `faces`. The maintainer ran
`mh tags` (heavy, duration not measured) and does not want to run it again.

**Names** (maintainer, 2026-10-25): *backup / restore*, the pair everybody knows. The verb
`backup` was the copy of the photos to the NAS: it becomes `mh push` first (0375, hence the
dependency: the two `backup` never coexist). The first draft of this TODO said `save` / `restore`.
`mh import` stays what it is (a file only a compared backup holds); the photos' own restore is
`mh pull` (0376).

What `/cache` holds and what is kept:

| Item | Kept | Why |
|---|---|---|
| `index.sqlite` | **yes** | the only costly item |
| `previews/` | no | rebuilt by the reports; can weigh GB (*estimated*) |
| `models/` | no | downloaded again (CLIP, face weights) |
| `shrink-try/`, `update-check.json`, czkawka cache | no | temporary |

From the tool folders:

- `config/` (`config.toml`, `people/*.toml`): **yes**, small; also protects from a bad edit.
- `mh.ps1` / `mh.sh`: **yes**, a few KB; it carries the list of photo folders (`launcher_kept`).
- `journal/`: **no** (maintainer's decision, 2026-10-24). It lives on `C:` outside the volume,
  so the risk this TODO covers does not reach it; `undo` also needs the quarantine, which is out
  of the question (size). Restoring an index next to the current journal is consistent:
  `journal_words` (0216) re-reads a journal whose size or mtime differs and drops the words of a
  journal gone.
- `nas-*.xml`: **no**. `Export-Clixml` encrypts with DPAPI: readable by the same Windows user on
  the same PC only (*to check* on the maintainer's PC, documented by Microsoft), so useless
  elsewhere; on this PC it is already outside the volume; and a password would travel in an
  archive copied to a USB stick. `mh` asks again at the first NAS access.

## What to do

1. **`mh backup [--to <folder>]`**: one archive
   `$HOME\media-hygiene\backups\mh-backup-YYYYMMDD-HHMMSS.zip` (`--to` a USB stick or the NAS:
   the default is on `C:`, like Docker's virtual disk, so it protects from a wrong move, not from
   a disk failure: say it in the 💡 line).
   - **Decision to take** (recommended): when `mh push` has a target (`push-target.txt`), the
     default goes there instead, in `<target>\.mh-backups\` (a folder `push` and `pull` skip):
     then one disk crash loses neither the photos nor the index, and the crash guide of 0376 has
     both in one place. Lost: the backup needs the NAS reachable (fall back to `$HOME`, said).
   - `index.sqlite` copied by SQLite's `backup` API inside the container (never a raw file copy
     of a database that may be open), `config/`, the launcher script, a `manifest.json` (image
     version, index schema version, SHA-256 of each member, row counts of the main tables).
   - Refused while another `mh` container runs (the containers carry labels, see
     `services/launcher_guards.py`): one line saying which.
   - Proven by reading back from disk: the archive reopened, `PRAGMA integrity_check` on the
     copied index, sizes and row counts shown (product rule: never "Saved" from memory).
   - The 3 most recent backups kept in the default folder, older ones removed (a named
     constant: say in the report whether it should be a setting); never pruned in a `--to`
     folder.
   - The `backups` folder is created by `mh` in the home; nothing goes under `/config`.
2. **`mh restore [<zip>] [--from <folder>]`**: the most recent backup of the default folder when
   none is given; `--from` a folder to look in (after a crash, `$HOME\media-hygiene` is new).
   - Checks the manifest and the SHA-256 first; refuses an index whose schema is newer than the
     image (say: `mh update` first); an older one is upgraded by `index/schema` at the next
     opening.
   - Before overwriting: an automatic `mh backup` of the current state (so a restore can itself
     be undone), said in the undo line.
   - Restores `index.sqlite` alone by default; `--config` restores `config/` too (it may have
     been edited since the backup). The launcher script is never overwritten: it is shown for
     comparison only (`mh folders` list), `mh update` rewrites it.
   - Same guard as `backup`: no other `mh` container running.
3. **Moves between backup and restore** (`.claude/rules/workflow.md`): files moved since the
   backup by `clean`, `sort`, `undo`, the quarantine, `pull` (0376) or the user (folder renamed in
   Explorer). The index is keyed by (path, size, mtime): the next audit prunes the paths gone and
   re-reads the new ones; write what happens to the `tags` / `descriptions` / `faces` rows of a
   moved file (`index/moves` follows the tool's own moves recorded in the journal?) and test each
   case.
4. CLI: verb page en + fr (`commands/backup.md` covering both verbs; one line saying it is not
   `--backup`, a folder compared, nor `push`), `reference-commands.md`, `COMMANDS_TOO`,
   `menu_catalog_*`, mkdocs `nav`; `--help` of both; `i18n_update` + French. `mh.sh` (WSL) the
   same way, `$HOME/media-hygiene/backups`.
5. Tests: backup → restore round trip (rows identical), a corrupted archive refused, a newer
   schema refused, the automatic backup before a restore, the 3-backup rotation, the guard
   against a running container, the cases of step 3.

## Acceptance

- `mh backup` then `docker volume rm media-hygiene-cache` then `mh restore`: the `tags`,
  `descriptions`, `meanings`, `faces` row counts are the same as before, and the next audit is
  incremental (no file hashed again).
- A backup shows its path, size and row counts read back from the archive.
- `docs_screenshots` to run for the new page (said, not run).

## Gain

Today, losing the volume means running every audit and `mh tags` again: hours on the
maintainer's collection (*estimated*; neither the index size nor the `mh tags` duration were
measured). With a backup: a restore in seconds to minutes, the time of copying `index.sqlite`
(*estimated*, size to measure with
`docker run --rm -v media-hygiene-cache:/cache:ro alpine sh -c "du -sh /cache/*"`).
