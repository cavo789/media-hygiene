# 0179 — `mh`: Windows does not go to sleep during a long run

- **Priority**: High
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/launcher_menu.py`, `documentation/{en,fr}/commands/launcher.md`, `documentation/{en,fr}/reference-troubleshooting.md`, `tests/unit/test_launcher_menu.py`
- **Needs maintainer**: one run on Windows: a laptop set to sleep after 1 minute stays awake through a `mh audit` longer than that, and sleeps again after (PowerShell 5.1)

## Why

A first audit of a large collection lasts longer than the usual sleep delay of a laptop
(15–30 min, estimated from Windows defaults: to check); the PC sleeps, Docker Desktop's VM
pauses, the run stops and the user does not know why. Asked by the maintainer (2026-10-16).

## What to do

- Around `docker run` in `mh.ps1`, call `SetThreadExecutionState(ES_CONTINUOUS |
  ES_SYSTEM_REQUIRED)` (kernel32, through `Add-Type`, works in Windows PowerShell 5.1 without
  admin: to check), and `ES_CONTINUOUS` alone in a `finally` so Ctrl+C restores it. The screen
  may still turn off (no `ES_DISPLAY_REQUIRED`).
- Only for the long commands (`audit`, `clean`, `inventory`, `classify`, `sort`, `tags`,
  `people`, `undo`: the list held by the script data, not by hand in the template).
- `Add-Type` costs a compile (~0.5 s, estimated): done once per session (`-not
  ('MhPower' -as [type])`).
- bash: `systemd-inhibit` when it exists (Linux), nothing on WSL (Windows decides) or macOS
  (`caffeinate -i` when it exists).

## Acceptance

- Unit: rendered PowerShell holds the call and its `finally` for the long commands only, ASCII;
  bash wraps with `systemd-inhibit` when a fake one is on `PATH`.
- Docs both languages: one line on the launcher page; troubleshooting entry "the analysis
  stopped overnight" points to it.

## Gain (estimated)

A first audit started in the evening: stopped at the first sleep → finished in the morning.

## Status — PARTIAL (2026-10-16)

### Done
- `LONG_COMMANDS` (`cli/safety.py`) → `LauncherCommands.long` → the script data; `mh.ps1` calls
  `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)` (`Add-Type` once per session,
  type `MediaHygiene.Power`) for those commands only, `ES_CONTINUOUS` alone in the `finally`.
- `mh.sh`: `systemd-inhibit --what=sleep` when present and logind answers (`--list`), not on
  WSL (`WSL_DISTRO_NAME`); `caffeinate -i` when present (macOS).
- Unit: PowerShell call and `finally`; bash with a fake `systemd-inhibit` (long command
  wrapped, `history` not, WSL not).
- Docs EN/FR: launcher bullet; troubleshooting "The analysis stopped overnight".
- `mh-measure.ps1` step 9b: polls `powercfg /requests` during `mh audit` (administrator only).

### Not done
- The check on Windows: a laptop set to sleep after 1 minute stays awake through `mh audit`,
  sleeps again after.
  **Reason:** needs the maintainer's Windows, from an administrator PowerShell:
  `powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 9 -Count 300`.

## Measured on Windows (2026-10-16), then removed from `mh.ps1`

`measures-20261016-1803`, step 9: the awake request was there during `mh audit` and gone after
(the mechanism worked), but Avast's Behavior Shield (`IDP.HELU.PSD11`) stopped the PowerShell
running `mh` during that audit, and afterwards refused any file at that folder's paths ("Access
denied", no new alert). The run-time compile of a kernel32 call is the likeliest trigger
(inferred, not isolated). Maintainer's decision: remove it from `mh.ps1`; the guides say to set
Sleep to Never for a first audit, and a troubleshooting entry covers the antivirus. `mh.sh`
keeps `systemd-inhibit` / `caffeinate`. To confirm: step 9 again in a new `-Work` folder, no
alert expected.

## Put back (maintainer, 2026-10-16)

The 18:17 run alerted again with a `mh.ps1` without the kernel32 call, and a user-like run
(`launcher`, `. mh.ps1`, `mh audit` in a normal PowerShell, no keep-awake) raised nothing: the
alerts came from the measure harness (`probe.ps1`, conhost, `-ExecutionPolicy Bypass`), not from
the compile. The keep-awake is back; still to check: the same user-like run with it.

## Status — DONE (2026-10-16, Windows measured)

User-like run (normal PowerShell, `. mh.ps1`, `mh audit --full`): `powercfg /requests` lists powershell.exe under SYSTEM during the audit; step 9b (measures-20261016-1803) showed it gone after. No Avast alert.
