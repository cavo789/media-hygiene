# 0184 — `mh.ps1`: UTF-8 console by default, accents and emojis readable

- **Priority**: High
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `tests/unit/test_launcher_menu.py`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: one run in the old console (conhost, not Windows Terminal) under Windows PowerShell 5.1: the `mh` menu in French shows `é` and the emojis, not `Ã©` or `?`

## Why

Windows PowerShell 5.1 decodes the output of a native program it captures (`$steps = @(mh
menu)`) with `[Console]::OutputEncoding`, the OEM code page (850 on a French Windows: to check)
while the image writes UTF-8. Not measured yet. The maintainer (2026-10-16): add the line by
default.

## What to do

- In the function of `mh.ps1`, before the first `docker` call: set
  `[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)` (and `$OutputEncoding` the
  same), saved first and restored in a `finally`, so the user's console is left as it was.
- The script itself stays ASCII (`launcher_ascii.py`).
- A step in `tests/measure/mh-measure.ps1` captures `mh menu` in conhost and writes whether it
  holds `é`.

## Acceptance

- Unit: rendered `mh.ps1` sets and restores the encoding, ASCII.
- Measurement step added.

## Gain (estimated)

French menu in the old console: unreadable accents (if confirmed) → readable.
