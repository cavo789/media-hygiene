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
