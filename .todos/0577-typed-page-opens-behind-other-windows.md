# 0577 — A page opened by a typed command (`mh review --intruders`) opens behind the other windows

- **Priority**: Low
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `tests/unit/test_launcher_comfort.py`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: a check on Windows (which window gets the focus)

## Reported (maintainer, 2026-10-30, from TODO 0510 point 1)

`mh review --intruders` typed in PowerShell: the page opened "well hidden".

## Read (2026-11-02)

`mh.ps1.j2:185` opens the page from a background job (`Start-Job` … `Start-Process $url`,
0178). Windows' foreground lock lets only the process that has the focus give it away: a job
(a hidden `powershell.exe`) does not have it, so the browser's new window or tab may stay behind
the console. Bringing it to front needs `SetForegroundWindow`/`AllowSetForegroundWindow`
(kernel32/user32 through `Add-Type`): a run-time compile, which Avast flags on the maintainer's
PC (memory `avast-on-maintainer-pc`). Not done in 0510.

## To do

1. Measure first (step in `mh-measure.ps1`): does the browser come to front when `Start-Process`
   runs in the console's own process instead of the job (the job only waits, then signals)?
2. If so, open from the main process once the job says the page answers; else leave as is and
   say on the console line "the page opened in your browser" (it may be behind).
