# 0279 — Browser does not open from the desktop shortcut

- **Priority**: high
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/cli/templates/mh.ps1.j2, src/media_hygiene/services/reviewing.py, src/media_hygiene/services/launcher_menu.py, tests/measure/mh-measure.ps1, tests/unit/ (launcher templates)
- **Needs maintainer**: a run of the new `mh-measure.ps1` step on the Windows PC (desktop shortcut, Windows PowerShell 5.1)

## Context

The maintainer double-clicked the desktop shortcut (2026-10-20). The console printed:

```text
✅ Accueil prêt, ouvrez http://127.0.0.1:8088/ dans votre navigateur. Ctrl+C l'arrête.
Votre navigateur s'ouvre sur http://127.0.0.1:8088/ ; sinon, ouvrez cette adresse.
```

No browser opened: the maintainer had to open the address by hand. Opening it is the intended
behaviour (0178): `mh.ps1.j2` starts a `Start-Job` that polls the page with
`Invoke-WebRequest` once a second for up to `BROWSE_WAIT` (300 s, `launcher_menu.py`), then
runs `Start-Process $url`. The second console line (`reviewing.py:160`) promises it.

## Hypotheses to check (none verified)

- The job runs in a child `powershell.exe`: from a shortcut (`-NoProfile`, hidden or minimised
  window) `Start-Process <url>` may not reach the user's default browser, or the job is never
  scheduled before `docker run` blocks the console.
- `Invoke-WebRequest` from the job fails every time (proxy settings, Avast — see the memory on
  it —, IE first-run engine in 5.1 despite `-UseBasicParsing`, `127.0.0.1` vs `localhost`), so
  the loop runs out after 300 s and gives up silently.
- The page answers the poll only after the slow start of 0277 (~45 s, estimated): it should
  still open later — did the maintainer wait?
- The finally block's `Remove-Job` kills the job if `docker run` returned early.

## Expected

1. Add a step to `tests/measure/mh-measure.ps1` that reproduces the job (same script block,
   started from a shortcut-like `powershell -NoProfile -WindowStyle Minimized`), logs each poll
   result and the `Start-Process` outcome to the results file.
2. Fix from what it shows (e.g. open the browser from the main runspace once the container
   prints its ready line, or `Start-Process` via `explorer.exe <url>`), keeping 0178's
   "open as soon as it answers".
3. When the browser cannot be opened, say so in one line instead of promising it: the second
   console line must not claim "Votre navigateur s'ouvre" when nothing will open.
4. A unit test on the rendered `mh.ps1` for the chosen mechanism; both languages' launcher
   pages updated if the behaviour text changes (`docs_screenshots` to rerun, unasked).
