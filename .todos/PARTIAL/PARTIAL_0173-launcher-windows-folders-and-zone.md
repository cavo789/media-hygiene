# 0173 — `launcher --photos "C:\Photos"`: Windows paths only, the time zone found by `mh`

- **Priority**: High
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_launcher.py`, `src/media_hygiene/services/launcher.py`, new `src/media_hygiene/services/launcher_folders.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher_memory.py`, `src/media_hygiene/config/zone.py`, new `src/media_hygiene/config/windows_zones.py` + `src/media_hygiene/config/data/` (CLDR `windowsZones`), `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/{en,fr}/clean/quick-guide.md`, `documentation/{en,fr}/start/03-several-folders.md`, `documentation/{en,fr}/commands/launcher.md`, `tests/unit/test_launcher*.py`, `tests/unit/test_zone*.py`, `tests/e2e/test_launcher_image.py`
- **Needs maintainer**: one run on Windows PowerShell 5.1 + Docker Desktop: the new `launcher` line, `mh audit`, `mh --photos "<a USB key>" audit`, a mistyped folder; check the times are local without `-e TZ`

## Why

The one long command of the guides still speaks Docker (maintainer, 2026-10-15):

```powershell
docker run --rm `
  -e TZ=Europe/Brussels `
  -v "C:\Photos:/data/c/Photos" `
  cavo789/media-hygiene launcher > "$HOME\media-hygiene\mh.ps1"
```

Four things to copy exactly: the zone, both sides of `-v` that must match (the guide needs a
whole box to explain "change both sides"), the redirection. The tool folders already default to
`$HOME\media-hygiene\…` (`launcher_script`) and a `-v …:/quarantine` is already kept; what is
left is Docker vocabulary.

## What the user types

```powershell
mkdir -Force "$HOME\media-hygiene"
docker run --rm cavo789/media-hygiene launcher --photos "C:\Photos" > "$HOME\media-hygiene\mh.ps1"
```

- `--photos` is repeatable (`--photos "C:\Photos" --photos "D:\Images\Famille"`), like
  `--prefer`/`--exclude`; no comma list (a folder name may hold a comma).
- `--quarantine "D:\quarantaine"`, once (one `/quarantine` mount point). On the photos' disk, a
  set-aside is a rename; elsewhere, a copy.
- The container side is computed with the existing convention (`paths/host_paths.py`):
  `C:\Photos` → `/data/c/Photos`; bash: `/mnt/c/Photos` → `/data/c/Photos`, `/home/me/Pictures`
  → `/data/home/me/Pictures`. `-v` keeps working (old guides, advanced users), merged with
  `--photos`.
- Refused with one line: a network path (`\\NAS\photos`: Docker Desktop bind mounts of UNC
  paths — to check), a relative path, a folder inside another one given (the same file twice:
  `paths/overlaps.py`).
- Name: `--photos`, not `--pictures`: the word of the whole tool and its documentation.

## What `mh` does

- Before each `docker run`: `Test-Path` (PowerShell) / `[[ -d ]]` (bash) on every photo folder;
  a missing one is said, nothing runs (Docker Desktop would create an empty folder and the
  audit would find nothing, silently).
- The time zone at each run: PowerShell 5.1 has `(Get-TimeZone).Id`, a Windows id
  (`Romance Standard Time`); .NET Framework cannot convert it to IANA (`TryConvertWindowsIdToIanaId`
  is .NET 6+). `mh.ps1` passes `-e MEDIA_HYGIENE_WINDOWS_ZONE=<id>`; the container maps it with
  the CLDR table `windowsZones.xml` (territory `001`, 142 zones counted in the file of
  2026-10-15, Unicode licence), vendored like the GeoNames data. bash passes the host's own zone
  (`$TZ`, else the target of `/etc/localtime`). Precedence: `[general] timezone` > `-e TZ` >
  the detected zone > UTC. A trip abroad then follows without writing `mh` again.
- `mh --photos "E:\Clé USB" audit`: one more folder for this command only (translated in
  PowerShell/bash, same rule as Python, tested against it), added to the remembered ones so the
  key's copies of the collection are found. To keep it: run `launcher` again.

## Acceptance

- Unit: `launcher --photos` (one, several, with `-v`, `--quarantine`), the refusals; the zone
  mapping (a Windows id → IANA, an unknown id → UTC, `TZ` wins); the bash `mh` really run with a
  fake `docker`: a missing folder stops, `--photos` added, the zone passed; the PowerShell
  script ASCII in French, its translation rule written the same as Python's.
- e2e: the launcher written with `--photos` on the demo tree, `mh audit` succeeds.
- Docs, both languages: the new line in "Clean in short" step 0, "Several folders", the
  `launcher` page; the box "change both sides of -v" goes; `docs_screenshots` to run.

## Gain (estimated)

From the command above: 4 things to copy exactly → 1 (the folder as Explorer shows it); the
`-v` explanation box and the zone sentence leave the first page of the guide.

## Status — PARTIAL (2026-10-15)

### Done
- `launcher --photos <folder>` (repeatable) and `--quarantine <folder>`
  (`services/launcher_folders.py`): the mount point by the tool's convention, WSL `/mnt/x/…`
  included; merged with the `-v` of the run; refused with one sentence: a network path, a
  relative path, a folder inside another (Windows folders compared without case). A refused
  folder writes a script that stops its own loading with the reason (`> mh.ps1` empties the
  file anyway), as the `-it` refusal does (`launcher_refusal.stopping_script`).
- `mh.ps1` / `mh.sh`: every photo folder checked before each `docker run` (a missing one is
  said, nothing runs; named volumes are not checked); `mh --photos <folder> <command>` adds a
  folder for that command only (PowerShell: `Resolve-Path`, drive letter in lower case,
  `\` → `/`; bash: `cd && pwd -P`, `/mnt/x` → `/data/x`).
- Time zone: `mh.ps1` passes `-e MEDIA_HYGIENE_WINDOWS_ZONE=$((Get-TimeZone).Id)` at each run,
  mapped by the vendored CLDR table (`config/data/windows_zones.tsv`, 142 zones, 7 old IANA
  links written with their current name: the image lacks `Europe/Kiev`, checked in
  `media-hygiene:latest`); `mh.sh` passes the host's `TZ` or the target of `/etc/localtime`.
  Precedence `[general] timezone` > `TZ` > the Windows zone > UTC. The variable is never
  carried into the suggested commands. `launcher` no longer advises `-e TZ`; its "mh
  remembers" line says the zone is read at each run.
- Tests: `tests/unit/test_launcher_folders.py` (mount points, refusals, several folders and the
  quarantine, nested, the PowerShell rule written in ASCII, the stopping script, the bash `mh`
  run with a fake `docker`: `--photos` gives the same mount point as Python, a missing folder
  stops, the zone passed; the zone table and its precedence).
- Docs, both languages: "Clean in short" step 0 (one line, the "both sides of -v" box replaced
  by "Several folders? A quarantine on another disk?"), "Several folders" (`mh` section),
  `commands/launcher.md`, `reference-commands.md` (two options), troubleshooting, the
  `timezone` setting.

### Not done
- One run on Windows PowerShell 5.1 + Docker Desktop: the new `launcher` line, `mh audit`,
  `mh --photos "<USB key>" audit`, a folder not plugged in, the report times local without
  `-e TZ`. The PowerShell part (`Resolve-Path`, `Get-TimeZone`, `Test-Path`, `@rest`) is only
  checked as text here: no PowerShell in the devcontainer.
  **Reason:** Needs maintainer (Windows machine).
  → step 15 of `tests/measure/mh-measure.ps1` added (inbox, 2026-10-16).
- An e2e test of `launcher --photos`: the demo tree lives in a named volume, and a host path of
  the devcontainer is invisible to the host Docker daemon. The existing e2e (`-v` volumes,
  `mh audit`, `mh` alone) covers the new templates.
  **Reason:** devcontainer limit; could run in CI only, with a host folder.
  → refiled as 0189, e2e in CI with a host folder (maintainer, inbox 2026-10-16).
- `docs_screenshots`: the `help-launcher.txt` capture (two new options) and the `-e TZ` line of
  the first audit's capture are stale.
  **Reason:** heavy (image build + browser), for the maintainer.
- Network folders (`\\NAS\photos`): refused by `--photos`; whether Docker Desktop can bind
  mount them, or a mapped drive letter, is to check.
  → keep the refusal: no network folders for now (maintainer, inbox 2026-10-16).

### Measured on Windows (2026-10-16, step 15 of mh-measure.ps1, PowerShell 5.1)
- 15a: the guide's `launcher --photos` line: exit code 0, `mh.ps1` written (33 590 bytes,
  holds `Get-TimeZone`). Its "launcher says" lines show PowerShell 5.1 wrapping docker's
  stderr in a NativeCommandError record: an artefact of the harness's `2>` redirect, not of
  the guide's line (`>` only, stderr on the console).
- 15b: `mh audit`: exit code 0.
- 15c: no hour read (the harness's `mh history` lists clean runs, none here: a harness bug).
  The local hour is shown by another run the same day: `mh audit` at about 18:54 local
  (Romance Standard Time, UTC+2) wrote `reports\20261016-185421-audit` — local, not UTC.
- 15e: a folder not plugged in (`Q:\…`): "cannot be found: plug its disk in, or write mh
  again with launcher", no docker run. Exit code 0 (the PowerShell `mh` sets none on that
  refusal; the bash one returns 2).
- Not done: 15d, `mh --photos <USB key> audit` (no key plugged in): with steps 12 and 13,
  `-OtherDrive E:`.
