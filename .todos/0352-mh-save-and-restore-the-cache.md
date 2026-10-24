# 0352 — `mh save` / `mh restore`: the index and the settings kept outside Docker's cache volume

- **Priority**: High
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/cli/templates/mh_save.ps1.j2`, `src/media_hygiene/cli/templates/mh_save.sh.j2`, `src/media_hygiene/cli/cmd_save.py`, `src/media_hygiene/services/cache_save.py`, `src/media_hygiene/services/cache_restore.py`, `src/media_hygiene/services/launcher_kept.py`, `src/media_hygiene/cli/menu_catalog_*.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/save.md`, `documentation/fr/commands/save.md`, `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`

## Context

Asked by the maintainer (2026-10-24): `/cache` is the named Docker volume `media-hygiene-cache`
(`services/launcher_kept.py`, `CACHE_VOLUME`). It is the only tool folder that is not in
`$HOME\media-hygiene\` (`config`, `journal`, `quarantine`, `reports`, `mh.ps1`, `nas-*.xml` are
there already). A `docker volume prune`, a reset of Docker Desktop or a reinstalled WSL erases it.
The index now holds work that is long to redo: besides digests, visual facts, metadata and video
fingerprints, the tables `tags`, `descriptions`, `meanings` and `faces`. The maintainer ran
`mh tags` (heavy, duration not measured) and does not want to run it again.

`mh backup` exists already (photos copied to the NAS, 0264) and `import` is a verb too: hence
`save` / `restore`.

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

1. **`mh save [--to <folder>]`**: one archive
   `$HOME\media-hygiene\saves\mh-save-YYYYMMDD-HHMMSS.zip` (`--to` a USB stick or the NAS:
   the default is on `C:`, like Docker's virtual disk, so it protects from a wrong move, not from
   a disk failure: say it in the 💡 line).
   - `index.sqlite` copied by SQLite's `backup` API inside the container (never a raw file copy
     of a database that may be open), `config/`, the launcher script, a `manifest.json` (image
     version, index schema version, SHA-256 of each member, row counts of the main tables).
   - Refused while another `mh` container runs (the containers carry labels, see
     `services/launcher_guards.py`): one line saying which.
   - Proven by reading back from disk: the archive reopened, `PRAGMA integrity_check` on the
     copied index, sizes and row counts shown (product rule: never "Saved" from memory).
   - The 3 most recent saves kept in the default folder, older ones removed (a named constant:
     say in the report whether it should be a setting); never pruned in a
     `--to` folder.
   - The `saves` folder is created by `mh` in the home; nothing goes under `/config`.
2. **`mh restore [<zip>]`**: the most recent save of the default folder when none is given.
   - Checks the manifest and the SHA-256 first; refuses an index whose schema is newer than the
     image (say: `mh update` first); an older one is upgraded by `index/schema` at the next
     opening.
   - Before overwriting: an automatic `mh save` of the current state (so a restore can itself
     be undone), said in the undo line.
   - Restores `index.sqlite` alone by default; `--config` restores `config/` too (it may have
     been edited since the save). The launcher script is never overwritten: it is shown for
     comparison only (`mh folders` list), `mh update` rewrites it.
   - Same guard as `save`: no other `mh` container running.
3. **Moves between save and restore** (`.claude/rules/workflow.md`): files moved since the save by
   `clean`, `sort`, `undo`, the quarantine or the user (folder renamed in Explorer). The index is
   keyed by (path, size, mtime): the next audit prunes the paths gone and re-reads the new ones;
   write what happens to the `tags` / `descriptions` / `faces` rows of a moved file (`index/moves`
   follows the tool's own moves recorded in the journal?) and test each case.
4. CLI: verb page en + fr (`commands/save.md` covering both), `reference-commands.md`,
   `COMMANDS_TOO`, `menu_catalog_*`, mkdocs `nav`; `--help` of both; `i18n_update` + French.
   `mh.sh` (WSL) the same way, `$HOME/media-hygiene/saves`.
5. Tests: save → restore round trip (rows identical), a corrupted archive refused, a newer
   schema refused, the automatic save before a restore, the 3-save rotation, the guard against
   a running container, the cases of step 3.

## Acceptance

- `mh save` then `docker volume rm media-hygiene-cache` then `mh restore`: the `tags`,
  `descriptions`, `meanings`, `faces` row counts are the same as before, and the next audit is
  incremental (no file hashed again).
- A save shows its path, size and row counts read back from the archive.
- `docs_screenshots` to run for the new page (said, not run).

## Gain

Today, losing the volume means running every audit and `mh tags` again: hours on the
maintainer's collection (*estimated*; neither the index size nor the `mh tags` duration were
measured). With a save: a restore in seconds to minutes, the time of copying `index.sqlite`
(*estimated*, size to measure with
`docker run --rm -v media-hygiene-cache:/cache:ro alpine sh -c "du -sh /cache/*"`).
