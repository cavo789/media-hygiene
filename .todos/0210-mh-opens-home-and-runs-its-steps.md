# 0210 — `mh` alone and the shortcut open the home page; `mh` runs the step chosen there, then the page again

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: 0209
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher_menu.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_launcher_menu.py`, `documentation/en/start/01-first-audit.md`, `documentation/fr/start/01-first-audit.md`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/commands/menu.md`, `documentation/fr/commands/menu.md`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: after the work, one run on Windows: the shortcut opens the home page; a button runs `mh clean` in the PowerShell window with its question; the page comes back after it; "⌂ Home" from a review page brings the home page back

## Context

Chosen by the maintainer on 2026-10-17 (proposal F5: the home page replaces the numbered menu).
0209 serves the page; a step's button ends it with exit code `100 + n`. Today `mh` alone captures
`mh menu`'s lines (`number<TAB>command`), reads a number with `Read-Host`, and runs `mh <step>`
with the step's mounts (0172); the Desktop shortcut and the right-click entry run `mh` alone
(0180, 0181).

What it changes for the user (said when the maintainer chose it): `mh` alone opens a browser page
(a few seconds) instead of the instant list in the terminal; `mh menu` keeps that list.

## What to do

- **The relay signal (set by the home page fix of 2026-10-17)**: `mh` must run `home` with
  `-e MEDIA_HYGIENE_LAUNCHER_STEPS=1` (constant `LAUNCHER_STEPS_VARIABLE` of
  `services/next_command.py`, never carried into a printed next command). Only then does a
  step's button end the server with `100 + n` (`services/home.py` `launcher_relays_steps()`,
  `HomeApp.relays_steps`). Without it the button reads *Copy*, copies the command and the page
  keeps running; `POST /api/step` answers 409. Set it **only** in the loop below, the one that
  reads the exit code: an `mh` that sets it without relaying brings back the bug the maintainer
  met (the page ended, nothing ran). Test: the bash `mh`'s `docker run` of `home` carries it;
  `mh home` typed alone (no loop) does not.
- `mh` alone (and so the shortcut and the right-click entry, `--photos` kept): run `home` as a page
  (the browser opens on it, 0178). When it exits:
  - `100 + n`: read the steps as today (`mh menu`, captured), run step `n` the way the menu does
    (`mh <step>` with its mounts, its questions in the terminal), then run `home` again;
  - 0 (⌂ Quit, Ctrl+C) or an error: end the loop, the exit code kept.
- A step that is itself a page (`review`, `places`…) opens on the same port: the home page's tab
  follows it (0209's polling), and its "⌂ Home" link ends it with 0, so `mh` runs `home` again.
- `mh menu` stays the terminal menu (no browser, a remote session, a slow PC).
- Both shells; Windows PowerShell 5.1 (no `&&`, `??`); messages through `launcher_menu.py`
  (shell-safe, translated).
- Step 14 of `mh-measure.ps1` (the menu by hand) gains the home page run described above.

## Explicit non-goals

- The page itself: 0209. The audit inside the page: 0211.

## Acceptance

- Unit (the bash `mh` with a fake `docker`, as `test_launcher_docker_down.py`): `home` exiting with
  103 runs step 3, then `home` again; 0 ends the loop; an error ends it with its code; the
  PowerShell text holds the same loop, ASCII.
- Docs both languages: step 1 (the shortcut opens the home page), the launcher and menu pages.
- Windows (maintainer): the run above.

## Gain (estimated)

Double-clicking Media Hygiene: a numbered list in PowerShell → the home page in the browser,
every step a button; the terminal only shows what a step prints and asks.
