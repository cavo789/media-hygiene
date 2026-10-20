# 0194 — A Media Hygiene icon for the shortcut and the right-click entry

- **Priority**: Low
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh_windows.ps1.j2`, `src/media_hygiene/services/launcher_host.py`, `src/media_hygiene/services/launcher.py`, `tests/unit/test_launcher_host.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`
- **Needs maintainer**: the icon itself (a drawing, or approval of one proposed), then one look on Windows at the Desktop icon and the right-click entry

## Why

Decided at the review of the 2026-10-16 run (question 3, about 0180/0181): `mh shortcut` and
`mh explorer` show PowerShell's icon. The maintainer wants one of the tool's own.

## What

- An `.ico` (16, 32, 48, 256 px) in the package; its licence stated if not drawn here.
- Where it lives on the host: `mh` cannot read the image's files, so `launcher` must write it
  (base64 in `mh.ps1`, decoded by `mh shortcut` into `$HOME\media-hygiene\media-hygiene.ico`
  before writing the `.lnk`)? Size of `mh.ps1` then: to measure (a 256 px icon is ~10–70 KB,
  estimated). Alternatives: `mh update`/`launcher` writes it next to `mh.ps1` once.
- `IconLocation` of both `.lnk` and the `Icon` value of the registry key point to it; read
  back as today; missing file → PowerShell's icon, said in one line.
- Avast: writing an `.ico` from a script is a new behaviour; check with a user-like run
  (memory of 2026-10-16: the harness, not `mh`, was flagged).

## Status — PARTIAL (2026-10-16)

### Done
- The icon, approved by the maintainer: `src/media_hygiene/cli/icon/` (`media-hygiene.svg`,
  a 16 px variant `media-hygiene-16.svg` drawn on the pixel grid, `media-hygiene.ico` 16/24/32/48/256
  px, 14.3 KB measured; `ICON.txt`: origin, MIT). In the wheel (checked with `uv build`).
- Delivery chosen by the maintainer: not base64 in `mh.ps1` (+~18 KB, a decoded blob written by
  a script looks like a dropper to an antivirus) but `_mh_icon`: `docker create` + `docker cp` of
  the image's `.ico` next to `mh.ps1`, `docker rm`; Docker writes the file, not PowerShell.
- `mh shortcut`: `IconLocation` of both `.lnk`, shown in the read-back; `mh explorer`: the `Icon`
  value of the key, shown after the read-back command. Not copied (and none from before) →
  PowerShell's icon and one translated line. Tests in `tests/unit/test_launcher_host.py`; docs EN/FR.

### Not done
- One look on Windows: the Desktop and Start menu icon, the right-click entry (16 px), how long
  `docker create`/`cp`/`rm` takes there (estimated 1–2 s), and whether Avast says anything.
  **Reason:** needs the maintainer's PC (Windows + Docker Desktop + Avast). Steps: `mh update`,
  then `mh shortcut` and `mh explorer`. If Explorer shows the old icon, its icon cache is stale
  (sign out and in again).

## Measured on Windows (2026-10-20, step 10 of mh-measure.ps1 at e4644f4, maintainer)

- Double-click on the Desktop *Media Hygiene* shortcut: window and home page open; no Avast or
  Defender alert. The right-click entry sits under *Show more options* (Windows 10.0.26300).
- Still open: the look of the icon (Desktop, Start menu, 16 px in the menu) and the
  `docker create`/`cp`/`rm` time (not asked by step 10).
