# 0264 — `mh backup`: copy the photo folders into a NAS folder of their own, only what it lacks, at Windows's SMB speed

- **Priority**: Medium — asked by the maintainer: "since I have a NAS, let me back up C:\Photos to it"
- **Batch**: actions
- **Depends**: 0245
- **Files**: `src/media_hygiene/plan/backup_target.py` (new), `src/media_hygiene/services/backup_run.py` (new), `src/media_hygiene/cli/cmd_backup.py` (new), `src/media_hygiene/cli/app.py`, `src/media_hygiene/console/backup_target_view.py` (new), `src/media_hygiene/actions/kinds.py`, `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/services/launcher_backup.py` (new), `src/media_hygiene/services/launcher_nas.py`, `src/media_hygiene/cli/templates/mh_backup.ps1.j2` (new), `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_folders.ps1.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_backup_target.py` (new), `tests/unit/test_launcher_backup.py` (new), `tests/integration/test_backup_run.py` (new), `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/backup.md` (new), `documentation/fr/commands/backup.md` (new), `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`, `tests/measure/mh-measure.ps1`

## Context

Asked by the maintainer on 2026-10-20, right after 0245 (the NAS in `mh`, read-only, and
`mh import`). 0245 goes **from** the NAS to the PC; this goes the other way: a backup of
`C:\Photos` and of every photo folder `mh` knows, into a folder of its own on the NAS (e.g.
`\\NAS\backup_photos`), never mixed with the NAS's existing `Photos` share (which stays a
`--backup` folder, compared and never changed).

The maintainer's three asks:

1. **Only what the NAS lacks** is copied (incremental).
2. What was removed from the PC is **proposed** for removal from the NAS, asked, never silent.
3. **Fast**: "FTP is ten times slower than SMB". Measured on 2026-10-20 (0245, step 21,
   DS216j over Ethernet, reads only): SMB from Windows 86–105.8 MB/s; SMB through a Docker
   CIFS volume 15.1 MB/s; FTP from Docker 15.2 MB/s. The limit is Docker Desktop's VM network,
   not the protocol: **the copy itself must be made by Windows** (`mh.ps1`), not the container.
   Writes to the DS216j were never measured (step 22 below).

What the tool brings over a plain `robocopy C:\Photos \\NAS\backup_photos /MIR` (built into
Windows, fast, resumable — and reused below for the bulk copy):

- a file moved by `sort` or renamed in Explorer is, for `/MIR`, a new file to copy and an old one
  to delete: after a first `sort`, the whole library goes over the network again;
- `/MIR` deletes on the NAS whatever left the PC, without asking or knowing why: a deletion by
  mistake in Explorer is propagated by the next run, which defeats the backup;
- a damaged or encrypted file (disk fault, ransomware) overwrites the good copy;
- it knows neither the excluded folders and names (`#recycle`, `@eaDir`, …) nor the quarantine.

## Design (proposed — see Decisions)

Same split as `mh phone` (0219): the container decides, Windows copies. The container never
writes on the NAS: it reads the target through 0245's CIFS volume, kept `ro`.

1. **The target, remembered once**: `mh backup --to \\NAS\backup_photos` the first time (or
   `mh folders add --backup-to`, to decide), kept in `mh.ps1` like 0245's NAS folders (host,
   share, user), reusing the password already kept for that NAS (`Export-Clixml`, this Windows
   user only). Refused, naming both, when it is, holds or lies in a photo folder or a `--backup`
   folder. Layout: one folder per source, `<target>\C\Photos\…` for `C:\Photos`, so two sources
   of the same name never meet.
2. **The plan, in the container** (`plan/backup_target.py`, `services/backup_run.py`,
   `media-hygiene backup`): from the index (the latest audit) and a listing of the target (size,
   date; 253 files listed in 0.1 s through Docker, measured in step 21):
   - same relative path, size and date on the target → nothing to do (as robocopy decides);
   - a target file at a path the PC no longer has, of the same size and date as a PC file at
     another path, and the same partial digest (first and last 64 KiB: 128 KiB read over the
     network, ≈ 9 ms at 15 MB/s, *estimated*) → a **move on the NAS** (a rename, no upload).
     Identical copies: ties broken by name, tested with the demo tree's copies;
   - the same path with another size or date (an edited file) → the NAS copy set aside first
     (see 5), then copied again; a PC file the audit found **broken** never replaces its NAS
     copy (listed apart);
   - a target file the PC no longer has at all → proposed for removal (see 5).
   Only the sources mounted and walked complete this run take part: a removable drive not
   plugged in, or a folder the walk could not read, leaves its part of the backup untouched
   (said in one line).
3. **Applied by Windows** (`cli/templates/mh_backup.ps1.j2`): the plan shown (counts, sizes),
   asked once; the moves and set-asides by `Move-Item` on the share (renames on the NAS); then
   one `robocopy <source> <target>\<drive>\<path> /E /MT:<n> /R:1 /W:1 /XD … /XF …` per source
   (the excluded folders and names, the quarantine; never `/PURGE` nor `/MIR`): only the files
   new or changed by size and date are copied, an interrupted run resumes at the next one.
   Robocopy's summary read back (copied, failed, bytes, MB/s); exit code ≥ 8 said as a failure
   in one line, never a stack. To check on the DS216j: dates kept to the second over SMB (else
   `/FFT`), paths over 260 characters.
4. **Proven by a closing container run**: the target listed again, every source file found with
   its size and date (a file failed by robocopy named), the run recorded (`history`, a new run
   kind `backup`); ends with the counts read back from the NAS and one 👉 line.
5. **Removals, asked apart**: the files the PC no longer has, counted by why, from what the
   tool already knows: purged (0216), deleted and confirmed in `review --gone` (0224), still in
   the quarantine, deleted but not yet confirmed, unknown. Proposed by default: purged and
   confirmed only; the others kept and counted. "Removed" means moved into
   `<target>\.removed\<date>\…` (a rename), emptied by `mh backup` after
   `[backup] keep_removed_days`; `undo <run>` puts them back.
6. **A safety stop**: when the removals plus the replaced files exceed
   `[backup] stop_above_percent` of the backup, nothing is applied; one line says why (a drive
   missing? many files changed at once?) and how to go on anyway.
7. A NAS powered off, a refused password, an older SMB: 0245's lines, unchanged. `mh.sh` (WSL, see Decided below):
   refused, said (as 0245 does for a share).
8. **Step 22 of `mh-measure.ps1`**: robocopy of 20 photos into `<target>\mh-measure-test\` with
   `/MT:1` then `/MT:8` (MB/s each), the time of 20 renames on the NAS, then that test folder
   removed; then `mh backup` twice on a test folder (the second copies nothing), one
   interrupted then resumed, one after a `sort` (renames only, no upload).

## Explicit non-goals

- Writing in a `--backup` folder: `\\NAS\Photos` stays read-only for every command (0205).
- Versions beyond one (`.removed` keeps the previous copy until `keep_removed_days`), encryption,
  compression: the NAS's own tools.
- Running on a schedule (Task Scheduler): a later TODO if wanted.
- Comparing the target in every audit (0204's "not in the backup"): it would hash the whole
  target over the network at 15 MB/s; `mh backup` itself says what it lacks.
- Restoring: `mh import` (0245) with the target declared `--backup` already copies back what
  only it holds.

## Decisions for the maintainer (proposed defaults)

1. **A NAS folder written by `mh`.** 0204, 0205 and 0245 all have "the tool never writes a
   backup; the user copies" as a non-goal. What this loses: "nothing on the NAS is ever written"
   stops being true for the target — a bug or a wrong path could change it. Kept: the container
   still reads the NAS `ro`; only Windows writes, only in the target, which may not overlap a
   `--backup` or photo folder. → **write the target** (default) or drop the TODO.
2. **The name**: `mh backup` (the maintainer's word) next to `--backup` (compared, never
   changed) may confuse; the docs would say "a backup you compare" vs "the folder `mh backup`
   fills". → **`mh backup --to`** (default) or another verb (`mh mirror`, `mh copy-to`).
3. **Where**: a new shared folder `backup_photos` created in DSM (default), or a folder inside an
   existing share (to check: a CIFS volume mounting a sub-folder of a share).
4. **What is copied**: every file of the photo folders minus the excluded folders and names and
   the quarantine (default: a PDF in `C:\Photos` is backed up too), or only what the audit reads
   (media and their sidecars).
5. **Removals**: purged and confirmed only, set aside in `.removed` and emptied after
   `keep_removed_days = 90` (default); or deleted at once (DSM's recycle bin may keep them if
   enabled on the share: to check).
6. **An edited file**: the previous NAS copy set aside in `.removed` (default) or overwritten.
7. **Proof of a copy**: size and date read back by the listing (default); a `--verify` re-reads
   each new copy and compares its SHA-256 (doubles the time of a run).
8. **Settings** (`config.toml`): `[backup] keep_removed_days = 90`, `stop_above_percent = 20`,
   `threads = 8` (robocopy `/MT`): settings (default) or constants.

## Acceptance

- Unit (`test_backup_target.py`): unchanged, new, edited, moved (by `sort`, by hand), moved
  identical twins, gone by each reason, a broken PC file, a source not mounted, the safety stop:
  each one planned as above.
- Integration (`test_backup_run.py`): a plan applied by a stand-in for the PowerShell part (moves,
  copies), the closing run proves it; a second run plans nothing; `undo` puts the removed back.
- Unit (`test_launcher_backup.py`): the rendered `mh_backup.ps1.j2` is ASCII, never holds
  `/PURGE` or `/MIR`, passes the excluded names, refuses an overlapping target.
- Docs both languages: `commands/backup.md` (+ `COMMANDS_TOO`, mkdocs `nav`), reference-commands,
  launcher page, step 3 ("Your NAS: back up your photos to it"), the time of a first backup from
  step 22. `docs_screenshots` to run afterwards.
- Windows (maintainer): step 22 run; a first real `mh backup` of `C:\Photos`, then a second
  that copies nothing.

## Gain (estimated)

- A first backup of the library (52,094 media, 240.9 GB: index of 2026-10-17, measured):
  through Docker at 15 MB/s (measured, SMB or FTP alike) ≈ 4 h 28 min; through Windows's SMB at
  ≈ 100 MB/s (measured for reads; writes to measure in step 22) ≈ 40 min — **−85 %** if the
  DS216j writes as fast as it reads.
- The next runs: a listing (≈ 21 s for 52,094 files, *estimated* linearly from 253 files in
  0.1 s) plus the new files only.
- After a `sort` that moves the whole library: `robocopy /MIR` sends 240.9 GB again (≈ 40 min,
  *estimated* as above) and deletes the old paths; `mh backup` renames on the NAS (seconds,
  to measure in step 22).
- A deletion by mistake is never propagated: only purged or confirmed removals are proposed,
  and they stay in `.removed` for `keep_removed_days`.

## Decided (2026-10-21)

The 8 proposed defaults, by the maintainer (`/todo:inbox`): the target folder is written by
Windows (robocopy), the container still reads the NAS `ro`; `mh backup --to`; a new DSM shared
folder `backup_photos`; every file of the photo folders minus the excluded folders/names and the
quarantine; removals purged or confirmed only, kept in `.removed` for `keep_removed_days = 90`;
an edited file's previous copy set aside in `.removed`; proof by size and date read back
(`--verify` optional, SHA-256); `[backup] keep_removed_days`, `stop_above_percent`, `threads` as
settings.

Note: step 22 of `mh-measure.ps1` already measures hard links (0213). The NAS write-speed
measurement does not exist yet: this TODO adds it as the next free step. The maintainer then
creates `backup_photos` in DSM and runs that step and a first real `mh backup` (the Windows part
of the Acceptance, after the implementation: an unattended run closes PARTIAL on it).

## Decided (2026-10-21) — `mh.sh` (WSL / Linux)

By the maintainer: **no backup from `mh.sh`**, no rsync. `mh backup` there is refused, clearly
and pedagogically (product rules: one 👉 What next line, translated en + fr):

- why, in one line: the copy is made by Windows, which writes to the NAS about 7× faster than a
  copy through Docker (measured, step 21: 86–105.8 MB/s against 15.1 MB/s);
- what to do, as a command to paste: open **Windows PowerShell** and run `mh backup --to
  \\<NAS>\backup_photos` (the same `mh`, written by the same install, with the same folders);
- the exit code says a refusal (non-zero), nothing is started.

Acceptance adds: a test running the rendered `mh.sh` with `backup`: the refusal text, the
PowerShell command in it, the exit code; the `commands/backup.md` page (en + fr) says
"Windows only" at the top, with the same command.
