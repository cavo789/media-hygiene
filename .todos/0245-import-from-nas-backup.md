# 0245 — `import`: copy into the library what only a backup (a Synology NAS) holds, never what the user already set aside or deleted

- **Priority**: Medium — asked by the maintainer: "there may be photos on the NAS that I do not have in C:\Photos"
- **Batch**: actions
- **Depends**: 0246, 0204, 0216, 0224
- **Files**: `src/media_hygiene/cli/templates/mh_nas.ps1.j2` (new), `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/plan/backups.py`, `src/media_hygiene/plan/backup_import.py` (new), `src/media_hygiene/services/import_run.py` (new), `src/media_hygiene/actions/kinds.py`, `src/media_hygiene/actions/copy_in.py` (new), `src/media_hygiene/cli/cmd_import.py` (new), `src/media_hygiene/cli/app.py`, `src/media_hygiene/console/backup_view.py`, `src/media_hygiene/report/backup_views.py`, `src/media_hygiene/services/launcher_folders.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_folders.ps1.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_backup_import.py` (new), `tests/integration/test_import_run.py` (new), `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/import.md` (new), `documentation/fr/commands/import.md` (new), `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`, `tests/measure/mh-measure.ps1`

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

## Measured on Windows (2026-10-20, step 21 of mh-measure.ps1, maintainer's Synology over Ethernet)

Share `Photos` (not `photo`), read-only, nothing written on the NAS:

| Way | Result |
|---|---|
| SMB from Windows (a drive mapped with the credential) | **works**: 253 files listed in 0.1 s, 20 photos read whole at **86–105 MB/s** |
| Docker given that drive letter | sees nothing (a mapped drive belongs to the Windows logon) |
| SMB mounted by Docker (CIFS volume) | **refused**: the NAS offers only legacy dialects ("Dialect not supported by server" for 3.1.1, 3.0, 2.1), which Docker Desktop's kernel forbids ("vers=2.0/1.0 mount not permitted when legacy dialects disabled") |
| FTP from Docker | **works at 15 MB/s**; names in **Latin-1** though FEAT says UTF8 (`F\xe9vrier 2023`); the NAS **closes the session** when a RETR is cut short (10 of 20 partial reads: a new login each, 0.45 s per photo for its first and last 64 KiB); MLSD, SIZE, MDTM, REST present |

- The design note "if SMB mounted by Docker works, reuse 0205's backup mount" is blocked by the
  NAS's SMB setting only: the maintainer tries DSM's *Maximum SMB protocol = SMB3* (2026-10-20),
  then step 21 again. If it works: the NAS is a `--backup` folder like any other (0205), no FTP
  module. If not: FTP as written above, with Latin-1 names and a new session after each
  partial read (or whole reads only), measured at 15 MB/s.
- The password: `mh-measure.ps1` keeps it with `Export-Clixml` (DPAPI, this Windows user only),
  at the maintainer's request; `mh` would need the same for a CIFS volume or FTP.

## Measured again after SMB3 (2026-10-20, step 21, DS216j, DSM *Maximum SMB protocol* set to SMB3 by the maintainer)

- **SMB mounted by Docker works**: CIFS volume `vers=3.1.1,sec=ntlmssp`, read-only; top folders
  and the 253 files of 2023 listed in 0.1 s; 20 photos read whole at **15.1 MB/s**.
- SMB from Windows: 105.8 MB/s; FTP from Docker: 15.2 MB/s. Both ways through Docker are 7 times
  slower than Windows whatever the protocol: the limit is Docker Desktop's VM network, not the NAS
  (measured, same run).
- (2,018.8 MB in Docker against 1,925.2 "MB" in Windows: the same bytes, MB against MiB.)

## Decision (maintainer, 2026-10-20) — replaces item 1's FTP design

- The NAS is reached by **SMB3 in a Docker CIFS volume**, read-only, and is then a `--backup`
  folder like any other (0204, 0205): no FTP module, no `remote/` package. Item 1's FTP part, its
  Latin-1 names and its partial reads are dropped (FTP measured and kept as a note only).
- `mh` creates the volume before each command that needs the NAS and removes it after, so the
  password never stays in Docker's volume options (as step 21 does); the password is asked once
  and kept with `Export-Clixml` (DPAPI: this Windows user on this PC only, as `mh-measure.ps1`
  does), never in `config.toml`, never in a log. `mh.sh`: the same with a file only the user can
  read, or asked each time — to decide while implementing.
- A NAS powered off: one line, the audit without it (item 1's last point stays).
- A NAS that offers only legacy SMB (as this one before the change): say the DSM setting to
  change (*Control Panel → File Services → SMB → Advanced → Maximum SMB protocol: SMB3*), the
  reason measured here: Docker Desktop's kernel refuses `vers=2.0` and `1.0`.
- Speed: reads at 15 MB/s (measured): only listings (size, date) for most files, the first and
  last 64 KiB for size matches, whole reads for partial-digest matches — as item 1 planned.
- **Remembered once, like any folder** (maintainer, 2026-10-20: "to make the NAS easier to
  use"): `mh folders add --backup \\NAS\Share` (or the folder window of 0201, which shows the
  network too) accepts a network path; `mh` keeps it in `mh.ps1` like the other folders
  (host, share, user), asks the password once, offers to keep it (encrypted for this Windows
  user, `Export-Clixml`, next to `mh.ps1`, never in `config.toml` nor in the repository),
  reads it back at each command, and says in one line where it is and how to forget it
  (`mh folders remove \\NAS\Share` deletes it too). `mh folders` lists the NAS with its state
  (answers / powered off), never the password. A wrong password, read back: said in one line,
  asked again, the kept one replaced only once the new one worked.
