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

Why Docker Desktop cannot see the drive (a removable drive plugged in after the WSL 2 VM started
is not mounted in it?): **to check** — the maintainer restarts Docker Desktop with the stick
plugged in (step 16 does it), then runs the `ls` again; the one-line advice of step 2 depends on
it (to confirm during the work, not blocking).

## What to do

1. `paths/host_sources.py`: a mount whose root is `/mnt/host/<drive>[/…]` and whose type is
   not `9p` is a drive Docker Desktop cannot see (measured shape above); keep its drive and
   folder (`D:\mh-test`) to name it. Today `_DESKTOP_ROOT` only knows `(/run)/desktop/mnt/host`.
2. Before an audit, clean, review, sort: such a folder stops the command with one line, e.g.
   *"Docker Desktop cannot see D:\mh-measure-11-backup: it shows an empty folder instead. Quit
   Docker Desktop and start it again with the drive plugged in."* — a backup or a photo folder
   alike; never a comparison with an empty folder.
3. `mh.ps1`: the same check before each run is cheap only from inside a container — prefer the
   tool's check (1–2); the launcher keeps checking the folder exists on Windows.
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
