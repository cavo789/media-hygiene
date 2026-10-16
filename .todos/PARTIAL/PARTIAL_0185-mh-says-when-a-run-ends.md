# 0185 — `mh`: the window title and a sound say when a long run ends

- **Priority**: Low
- **Batch**: launcher
- **Depends**: 0179
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher_menu.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/{en,fr}/commands/launcher.md`, `tests/unit/test_launcher_menu.py`
- **Needs maintainer**: one run on Windows: the title reads "mh audit…" during the run, "mh audit: done" (or "failed") after, a sound plays (PowerShell 5.1)

## Why

A first audit takes hours; the window is minimised. The user should see in the taskbar that it
is running, then that it is over. Asked by the maintainer (2026-10-16).

## What to do

- For the long commands of 0179 (same list): before `docker run`, `$Host.UI.RawUI.WindowTitle =
  "mh <command>..."`; after, "mh <command>: done" or "failed" from `$LASTEXITCODE`, and
  `[System.Media.SystemSounds]::Asterisk.Play()` (`Hand` on failure). The previous title is
  restored at the next `mh` call, not at the end (the point is to read it later).
- Texts translated, ASCII in the script (`launcher_ascii.py`).
- bash: the title escape `\e]0;…\a` and the bell `\a`.

## Acceptance

- Unit: rendered scripts set the title before and after, sound on long commands only.
- Docs both languages: one line on the launcher page.

## Gain (estimated)

Knowing a long run ended: open the window to check → see it in the taskbar, hear it.

## Status — PARTIAL (2026-10-16)

### Done
- `mh.ps1`, long commands only: title `mh <command>...` before `docker run`, `mh <command>:
  done` / `failed` (translated, `MenuTexts.done` / `failed`) in the `finally`, then
  `SystemSounds.Asterisk` / `Hand`; the user's title saved in `$global:MediaHygieneTitle` and
  restored at the next `mh` call.
- `mh.sh`: title escape `\e]0;…\a` and a bell, only when stderr is a terminal; the status of
  `docker run` is still returned.
- Unit: rendered PowerShell (French texts expanded), bash status kept.
- Docs EN/FR: one bullet on the launcher page.
- `mh-measure.ps1` step 9c: logs the title after `mh audit` and at the next call; asks
  whether the sound was heard.

### Not done
- The check on Windows (title in the taskbar, sound) under PowerShell 5.1.
  **Reason:** needs the maintainer's Windows: `powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 9 -Count 300`.
