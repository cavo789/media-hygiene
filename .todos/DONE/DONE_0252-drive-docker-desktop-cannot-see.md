# 0252 — A drive Docker Desktop cannot see is mounted empty: say so, never compare with nothing

- **Priority**: High — an audit said the photos were missing from a backup that held them all
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/paths/host_sources.py`, `src/media_hygiene/paths/mounts.py`, `src/media_hygiene/services/data_checks.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `tests/unit/test_host_sources.py`, `tests/unit/test_data_checks.py`, `documentation/en/reference-troubleshooting.md`, `documentation/fr/reference-troubleshooting.md`, `tests/measure/mh-measure.ps1`

## Context

Measured by the maintainer on 2026-10-19 (mh-measure step 11h, image of PR #15):

- Backup on a USB stick plugged in after Docker Desktop started (`D:\mh-measure-11-backup`, 5
  photos): `mh` said `found` (checked on the Windows side), but the container saw an **empty**
  folder: `mh audit` scanned 3 files (the library only) and said *"3 files of your photos are not
  in this backup"* — false, the stick held copies of all of them.
- `docker run -v "D:\mh-test:/data/d/mh-test:ro" … ls` with 2 photos copied there: an empty folder;
  `/proc/mounts`: `/dev/sdf /data/d/mh-test ext4 ro,…` — a folder of Docker Desktop's own virtual
  disk, not a host share. Docker Desktop created it silently.
- `/proc/self/mountinfo` of one container with both (measured, maintainer's PC):
  ```
  1377 1365 0:99 /Temp /data/c/temp ro,noatime - 9p C:\134 rw,aname=drvfs;path=C:\;…
  1378 1365 8:80 /mnt/host/d/mh-test /data/d/mh-test ro,relatime - ext4 /dev/sdf rw,discard,…
  ```
  A drive Docker Desktop shares is `9p` with `aname=drvfs`; one it cannot see has the root
  `/mnt/host/<drive>/<folder>` on the VM's own `ext4` disk: the folder Docker Desktop created.
- The same step with the backup on `C:`: 8 files scanned, "every file of your photos is in this
  backup" (the comparison is right; only the mount was empty).
- Same risk for a **photo folder** on such a drive: seen empty, nothing to clean (no data loss),
  but a wrong picture of the library. And for a quarantine drive.

Why (2026-10-19): **WSL mounts fixed drives only.** The stick is `FAT32`, `DriveType Removable`
(`Get-Volume`, measured); Microsoft's WSL configuration page says automount mounts *fixed* drives
under `/mnt`, a removable one must be mounted by hand (`mount -t drvfs D: /mnt/d`). Measured: the
folder stayed empty after Docker Desktop was restarted twice with the stick plugged in (step 16);
`wsl -d docker-desktop ls /mnt/host` lists `d`, but only as the folder Docker Desktop created.
Most external hard disks and SSDs report `Fixed` and are shared (*to check* on one).
**Mounting it by hand works** (measured, same evening): `wsl -d docker-desktop sh -c "mount -t
drvfs D: /mnt/host/d && ls /mnt/host/d/mh-test"` listed the 2 photos, and the same `docker run -v
"D:\mh-test:…"` then saw them (sizes and 2020 dates right). The mount lasts until Docker Desktop
stops (*to check*: whether it blocks Windows' "safely remove" of the stick).

## What to do

1. `paths/host_sources.py`: a mount whose root is `/mnt/host/<drive>[/…]` and whose type is
   not `9p` is a drive Docker Desktop cannot see (measured shape above); keep its drive and
   folder (`D:\mh-test`) to name it. Today `_DESKTOP_ROOT` only knows `(/run)/desktop/mnt/host`.
2. Before an audit, clean, review, sort: such a folder stops the command with one line, e.g.
   *"Docker Desktop cannot see D:\mh-measure-11-backup (a removable drive, such as a USB stick):
   it shows an empty folder instead. Copy it to a fixed disk, or use an external hard disk."* —
   a backup or a photo folder alike; never a comparison with an empty folder. The launcher can
   say it earlier: `(Get-Volume -DriveLetter D).DriveType -eq 'Removable'` when a folder is added.
3. `mh.ps1` (Windows): before a `docker run`, for each mounted folder on a drive whose
   `(Get-Volume -DriveLetter X).DriveType` is `Removable`, mount it in Docker Desktop's VM when it
   is not yet (`wsl -d docker-desktop sh -c "mountpoint -q /mnt/host/x || { mkdir -p /mnt/host/x &&
   mount -t drvfs X: /mnt/host/x; }"`), one line said (*"D: is a removable drive: shared with
   Docker Desktop"*); a failure says the line of step 2 and stops. Measured to work on FAT32.
   Check with Avast (no `-ExecutionPolicy Bypass`, no Add-Type: `wsl.exe` only). The tool's
   check (1–2) stays for every other case (mh.sh, a `docker run` by hand, a mount that failed).
4. Troubleshooting page (en + fr): the symptom ("missing from the backup", "0 files") and the fix.
5. mh-measure step 11h: log the mount type of the backup in the container (`grep /data
   /proc/self/mountinfo`), so a run on a stick tells at once.

## Acceptance

- Unit tests: a mountinfo with a `9p`/desktop mount and an `ext4` `/dev/sdX` one under `/data`:
  the second is reported; a Linux run without Docker Desktop (every mount local) reports nothing.
- The maintainer's step 11 with `-OtherDrive D:` on a stick plugged in after Docker Desktop: the
  command stops with the line above; after a restart of Docker Desktop, the audit finds the 5 files.

## Gain

A backup check that can no longer report a false "missing" (measured: 3 of 3 photos falsely
missing); the user told the fix in one line instead of a wrong report.

Command used for the mountinfo above (stick plugged in):

```powershell
docker run --rm -v "D:\mh-test:/data/d/mh-test:ro" -v "C:\temp:/data/c/temp:ro" --entrypoint sh media-hygiene -c "grep ' /data' /proc/self/mountinfo"
```

## Decided (2026-10-19)

**Mount it and say so** (maintainer): `mh.ps1` mounts a removable drive in Docker Desktop's VM itself (`wsl.exe`, measured to work), one line said; a failure stops with the advice. Alternatives left aside: warn only; ask each time.

## Status — DONE (2026-10-19)

### Done
- `paths/host_sources.py` `unseen_drive_folder`: a mount whose root is
  `/mnt/host/<drive>[/…]` and whose source is a block device (`/dev/…`, the VM's own disk)
  is a drive Docker Desktop cannot see; `MountTable.unseen_drives` keeps its point and its
  Windows folder (`D:\mh-test`).
- `services/unseen_drives.py`: `refuse_empty_data` (audit, review, classify, the home
  audit) and `ensure_can_act` (clean, sort, undo, album, xmp) stop with one line naming the
  folders, the tip giving `mh` and the `wsl -d docker-desktop … mount -t drvfs` line.
- `mh.ps1`: before each `docker run`, every drive of the folders mounted (but C:) whose
  `Get-Volume` DriveType is `Removable` is mounted in Docker Desktop's VM
  (`wsl.exe -d docker-desktop sh -c "mountpoint -q … || { mkdir -p … && mount -t drvfs X: …; }"`),
  one line said; a failure stops with the advice.
- Troubleshooting page (en + fr): the symptom and the fix. mh-measure step 11h: the drive's
  type, the mountinfo and the files seen by a container before and after `mh`, mh audit's
  lines.
- Review of 2026-10-19 (2), commit a63e789: after each command (`finally`, after the
  `docker run`), `mh.ps1` unmounts the removable drives this run mounted itself (the mount
  line exits 10 when the drive is mounted already: another window, or by hand), so Windows
  can eject the stick. Every container using a removable drive carries
  `--label media-hygiene.drive.<x>=1`; one still running → the drive left mounted, one line.
  A failed `umount` says one line, the exit code stays the run's. mh-measure 11h logs the
  VM's mount after `mh audit` (expected: none), 11j asks whether Windows ejects the stick.

### Not done
- The maintainer's step 11 on a stick plugged in after Docker Desktop. **Reason:** Windows +
  a USB stick, with the image of this branch: `Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/a63e789/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1; Unblock-File .\mh-measure.ps1`, then
  `.\mh-measure.ps1 -Only 11 -Count 20 -OtherDrive D:` (D: the stick). To check there too:
  `mountpoint` exists in the docker-desktop distribution; whether Windows lets the stick be
  safely removed after the run (step 11j, still waiting after the review).
- mh.sh (WSL, Linux): no drive mounting (a WSL user mounts `/mnt/x` by hand); the tool's
  check covers it.

## Inbox (2026-10-19)

- mh.sh (WSL) mounting a removable drive → refiled as 0254 (maintainer).

### Measured (2026-10-19, step 11, image 47a411fa built from main a21f880, USB stick FAT32 Removable in D:)
- Run 1 (`measures-20261019-2138`): D: was already mounted by hand earlier (9p before mh): mh left it
  (not its own), the audit scanned **8** files, "every file of your photos is in this backup"; the
  stick could not be ejected ("This device is currently in use") — the hand mount; after
  `wsl -d docker-desktop umount /mnt/host/d`, Windows ejected it at once: the VM's mount is what
  blocks the eject.
- Run 2 (`measures-20261019-2153`), stick not mounted: before mh, an empty `ext4` folder (0 files);
  "D: is a removable drive: shared with Docker Desktop."; audit **8** files, all in the backup;
  after the command, D: no longer mounted in the VM; clean left the 5 files; **ejected safely: y**.
- Before → after: 3 of 3 photos falsely "missing" and a stick that could not be ejected → the right
  comparison, the stick free after each command.
