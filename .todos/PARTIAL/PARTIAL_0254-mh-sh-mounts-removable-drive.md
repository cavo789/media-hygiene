# 0254 — `mh.sh` (WSL): a removable drive is mounted for the user, as `mh.ps1` does

- **Priority**: Low — the maintainer's public is Windows PowerShell; the tool already refuses a folder Docker sees empty (0252)
- **Batch**: launcher
- **Depends**: 0252
- **Files**: `src/media_hygiene/cli/templates/mh_guards.sh.j2`, `src/media_hygiene/cli/templates/mh_host.sh.j2`, `src/media_hygiene/services/launcher_guards.py`, `documentation/en/reference-troubleshooting.md`, `documentation/fr/reference-troubleshooting.md`, `tests/unit/test_launcher_guards.py`, `tests/measure/mh-measure.ps1`

## Context

0252: a USB stick plugged in after Docker Desktop started is mounted empty in containers;
`mh.ps1` now mounts it in Docker Desktop's VM (`wsl.exe -d docker-desktop … mount -t drvfs`)
and says so. `mh.sh` (WSL) does nothing: WSL itself only mounts fixed drives under `/mnt/x`
(step 16, 2026-10-19), so a WSL user mounts the stick by hand and the tool refuses the empty
folder with advice. Maintainer's choice (inbox 2026-10-19): `mh.sh` does it too.

## What to do

1. To check first, on Windows + WSL + Docker Desktop (a step of `mh-measure.ps1` running `wsl`):
   - which mount a container sees for `-v /mnt/e/Photos:…` from a WSL distro with Docker
     Desktop's integration: the distro's `/mnt/e`, or Docker Desktop's `/mnt/host/e`? The fix
     differs: mount in the user's distro (`sudo mount -t drvfs E: /mnt/e`, needs sudo) or in
     the `docker-desktop` distribution (reachable from WSL as `wsl.exe -d docker-desktop`
     through interop, no sudo);
   - whether `wsl.exe` interop is enabled in the user's distro (it can be turned off in
     `/etc/wsl.conf`).
2. In `mh_guards.sh.j2`, before each `docker run`: for each `/mnt/<x>` photo folder that is
   empty or absent while the drive exists on Windows (`cmd.exe /c vol X:` or
   `powershell.exe Get-Volume`, via interop), mount it where step 1 says, one line said; a
   failure (no sudo, interop off) stops with the advice of 0252. Native Linux (no `wsl.exe`):
   nothing changes.
3. Tests: bash with fake `wsl.exe`/`mount`/`docker` (mounted, already mounted, failure, native
   Linux). Docs en + fr: the troubleshooting entry for WSL.

## Acceptance

- From WSL, `mh audit` on a stick plugged in after Docker Desktop: the line "drive E: shared
  with Docker" and the stick's files counted, or one clear line when it cannot.

## Status — PARTIAL (2026-10-19)

### Done
- `mh.sh` (`mh_drives.sh.j2`, included by `mh.sh.j2`): before the container, each `/mnt/<x>`
  photo folder (the folders of `mh`, and `--photos`) whose drive is not a mount point in the
  distribution while Windows has it (`cmd.exe /c vol X:`, through interop) is mounted with
  `sudo mkdir -p /mnt/x && sudo mount -t drvfs X: /mnt/x -o uid=…,gid=…` (owned by the user, as
  WSL's own mounts), one line said; a failure stops the command with the line to type. C: is
  never asked; native Linux, macOS or interop off (no `cmd.exe`): nothing changes, the
  "cannot be found" line as before.
- `mh` became a small wrapper (`local mounted marks`) around `_mh_command`: the drives mounted
  are unmounted after every command whatever the way out (`sudo umount`), left mounted while
  another `mh` container carries the drive's label (`media-hygiene.drive.x`, also put on the
  run); a failed unmount says the line to type before ejecting.
- Choice from step 1 left open: the mount is made in the user's distribution, not in Docker
  Desktop's VM: `mh.sh` itself checks the folder exists there before `docker run`, so it must
  be mounted there in any case.
- Tests: `tests/unit/test_launcher_wsl_drive.py` (fake `mountpoint`, `cmd.exe`, `sudo`,
  `docker`: mounted then unmounted, labelled once, already mounted, native Linux, not a drive
  of Windows, sudo refused, another mh using it, unmount refused, C:). Docs en + fr:
  troubleshooting, *A USB stick is seen empty*.

### Not done
- Step 1 of the TODO: whether a container started from WSL sees the distribution's `/mnt/e`
  once mounted there (what `mh.sh` now does), or only Docker Desktop's `/mnt/host/e`; then the
  acceptance (the stick's files counted, Windows ejecting it after).
  **Reason:** Windows + WSL + Docker Desktop and a USB stick only. Step 11k of
  `tests/measure/mh-measure.ps1` answers it (interop, `/mnt/x` before, the files a container
  from WSL sees before and after `mount -t drvfs` in the distribution, then the eject of 11j).
  If the container sees nothing, `_mh_drive` must mount in `docker-desktop` too
  (`wsl.exe -d docker-desktop`, as `mh.ps1`). Command (PowerShell 5.1, a stick as E:):
  `Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/COMMIT/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1`,
  `Unblock-File .\mh-measure.ps1`, then `.\mh-measure.ps1 -Only 11 -Count 20 -OtherDrive E:`.
