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
