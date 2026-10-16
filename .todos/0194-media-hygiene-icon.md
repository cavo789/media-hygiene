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
