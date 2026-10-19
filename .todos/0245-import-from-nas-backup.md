# 0245 — `import`: copy into the library what only a backup (a Synology NAS) holds, never what the user already set aside or deleted

- **Priority**: Medium — asked by the maintainer: "there may be photos on the NAS that I do not have in C:\Photos"
- **Batch**: actions
- **Depends**: 0246, 0204, 0216, 0224
- **Files**: `src/media_hygiene/remote/ftp_source.py` (new), `src/media_hygiene/remote/ftp_index.py` (new), `src/media_hygiene/plan/backups.py`, `src/media_hygiene/plan/backup_import.py` (new), `src/media_hygiene/services/import_run.py` (new), `src/media_hygiene/actions/kinds.py`, `src/media_hygiene/actions/copy_in.py` (new), `src/media_hygiene/cli/cmd_import.py` (new), `src/media_hygiene/cli/app.py`, `src/media_hygiene/console/backup_view.py`, `src/media_hygiene/report/backup_views.py`, `src/media_hygiene/services/launcher_folders.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_folders.ps1.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_backup_import.py` (new), `tests/integration/test_import_run.py` (new), `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/import.md` (new), `documentation/fr/commands/import.md` (new), `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: the results of step 21 of `mh-measure.ps1` (0246): SMB mounted by Docker, SMB in Windows only, or FTP — which design to build, and the read speeds (step written on branch `iterate/2026-10-19`; image built from that branch; PowerShell: `cd C:\temp`, `Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/iterate/2026-10-19/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1`, `Unblock-File .\mh-measure.ps1`, `.\mh-measure.ps1 -Only 21 -Count 1 -Nas <IP> -NasShare photo -NasUser <user>`)

## Context

Asked by the maintainer on 2026-10-19, next to 0219 (`mh phone`). The NAS (Synology) is their
backup, so it holds a copy of almost everything in `C:\Photos`, but perhaps also photos the
library no longer has (or never had). Those should be found and proposed for copy into
`C:\Photos` — **except** the ones the user already dealt with: set aside in the quarantine,
purged, or deleted.

Not an extension of 0219: a phone over USB is only seen by PowerShell (MTP), so 0219 compares by
name and size. A NAS share is a folder Docker can read, so the comparison is **by content**, with
what already exists:

- 0204, the backup role: a `--backup` folder is read, compared by content, never changed, and the
  audit already lists "only in the backup" (`plan/backups.py`, `backup-only.csv`);
- 0205: `mh` mounts a backup `:ro` for every command (open, Depends);
- 0216: the files set aside by a choice are remembered by content (size, SHA-256) in the
  journals, `purge` included (it erases the quarantine, never the journal);
- 0224: the files deleted in Explorer are kept in the index's gone rows (size, partial digest,
  full digest when known).

What is missing: (1) "only in the backup" does not subtract what the user already dealt with,
(2) the tool never copies (0204's non-goal: "the user copies"), (3) the NAS is reached over
**FTP** (maintainer, 2026-10-19): Docker cannot mount an FTP server as a folder, so the backup
role, which reads a mounted folder, cannot see it as it is.

## What to do

1. **Reach the NAS over FTP** (`remote/ftp_source.py`, Python's `ftplib`, stdlib): the container
   connects itself (`[backup] ftp = "ftp://nas.local/photo"` or `--backup-ftp`; the password
   asked once by `mh` and passed as an environment variable, never in `config.toml`, never in a
   log; plain FTP: the NAS is plugged into the PC only, FTPS not needed — maintainer, 2026-10-19). Nothing is mounted, so
   nothing can be written: only `MLSD` (list), `RETR` (read) and `REST` (read from an offset) are
   ever sent — a test checks no other command exists in the module.
   The comparison follows the exact pipeline without downloading the NAS:
   - the listing gives each file's size and date (`MLSD`): a size that no library file, no
     remembered content and no gone file has proves the file is **new**, without reading it;
   - the others: the first and last 64 KiB read (`REST` + `RETR`, aborted after 64 KiB) give the
     partial digest; only files whose partial digest matches are read whole for the SHA-256;
   - kept in the index under `ftp://host/path` keyed by (path, size, mtime) (`remote/ftp_index.py`):
     the next run reads only what changed on the NAS.
   `@eaDir` and `#recycle` skipped as on a disk (`excluded_names`).
   **If step 21 (0246) shows SMB mounted by Docker works**: mapping it as a drive letter and
   using 0205's `:ro` backup mount reuses everything as it is; FTP stays the way when it does not.
   **The NAS is powered off most of the time** (maintainer, 2026-10-19): when it does not answer,
   say it in one line ("The NAS does not answer: power it on, then `mh import` again"), never a
   traceback, and the audit without it stays as it is.
2. **What only the NAS holds, minus what was dealt with** (`plan/backup_import.py`, called by
   `plan/backups.py`, 178/200): a file of "only in the backup" is **not** proposed when its
   content is
   - remembered as set aside (0216's set: burst, near, chosen, unwanted, returned — quarantined
     or purged);
   - a gone file (0224), confirmed or still waiting for `review --gone`: either deleted on
     purpose, or moved to a disk not plugged in — not to import in either case; matched by size
     and full digest when known, else size and partial digest (the first and last 64 KiB), as
     `services/returned.py` already does (`by_partial`);
   - an exact copy set aside: its kept copy is in the library, so it is not "only in the backup"
     already.
   Each excluded count said apart, so a deletion by mistake can still be recovered by hand:
   "1,240 photos only on the NAS: 37 never seen in your library (210 MB) → `mh import`;
   1,180 set aside before, 23 deleted in Explorer: not proposed".
3. **Near copies** (decision below): a NAS file whose near copy is in the library (HEIC on the
   NAS, JPG in `C:\Photos`; a resized copy) is "probably already there", listed apart, not
   proposed by default.
4. **`media-hygiene import`** (new verb, `mh import`): shows the list (count, size, the first
   ones; the report section gains them with previews), asks once, then copies into
   `<first photo folder>\From NAS\<the NAS's folders kept>` (or `--to`). Each copy written to a
   temporary name, its SHA-256 compared with the source, then renamed; journaled under a new
   kind `copy-in` so `undo` removes the copies (never touches the NAS). Ends with the count read
   back from the destination and `👉 mh audit`. Refuses without a persistent `/journal`, like
   `clean`.
5. The next audit finds nothing left to import (the copies are now in the library).

## Explicit non-goals

- Writing anything on the NAS (read-only FTP commands, or an `:ro` mount with SMB).
- Sorting the imported files: `classify` / `sort`, as for any folder.
- Synology Photos' own database or albums: only the files of the share.

## Decisions for the maintainer (proposed defaults)

- Near copies on the NAS (HEIC vs JPG): **not proposed, listed apart** (default) — or proposed.
- Gone files not yet confirmed in `review --gone`: **not proposed** (default) — or proposed until
  confirmed.
- Destination: **`C:\Photos\From NAS\…`, NAS folders kept** (default) — or straight into the
  matching year folders.

## Acceptance

- Unit (`test_backup_import.py`): a library, a backup, journals and gone rows: a file only in the
  backup is proposed; remembered (quarantined, purged), gone confirmed, gone waiting, near copy:
  each one not proposed and counted apart; identical copies inside the backup proposed once.
- Integration (`test_import_run.py`): copy verified, journaled, `undo` removes it, the backup
  unchanged; a second audit proposes nothing.
- Docs both languages: `commands/import.md` (+ `COMMANDS_TOO`, mkdocs `nav`), step 3 ("Your NAS:
  get back what only it holds"), the time of a first audit over the network. `docs_screenshots`
  to run afterwards.
- Unit (`ftp_source`): against a local FTP server in the test (`pyftpdlib`, dev dependency, to
  check its licence) or a fake: listing, partial reads, a new file never downloaded.
- Windows (maintainer): step 21 of `mh-measure.ps1`, extended — `mh audit` with the NAS over FTP, `mh import`
  twice (the second copies nothing), the time of each.

## Gain (estimated)

Today: the NAS must be compared by hand or excluded; nothing tells the photos lost from
`C:\Photos` from those deleted on purpose. After: one list of the photos never dealt with,
copied and verified in one command. Time of a first comparison over FTP: the files of a size unique on the NAS are never
read; the others cost 128 KiB each, and only the true copies are read whole — estimated ≈
110 MB/s on gigabit Ethernet (to measure), so ≈ 45 min for 300 GB of true copies at worst; the
next runs read only what changed (index keyed by path, size, mtime).
