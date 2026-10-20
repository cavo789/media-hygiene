# 0276 — Warn when mh.ps1 changed on disk since it was loaded

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/cli/templates/mh.ps1.j2, src/media_hygiene/cli/templates/mh.sh.j2, src/media_hygiene/services/launcher_host.py, documentation/en/commands/launcher.md, documentation/fr/commands/launcher.md

## Context

On 2026-10-20 the maintainer rebuilt the image and wrote mh.ps1 again with `launcher`, but
did it from a PowerShell window that already had the old `mh` loaded. `mh shortcut` then ran
the old function in memory: it printed the old, verbose read-back (fixed in dfc476b) and
rewrote the shortcuts with `-ExecutionPolicy Bypass` (removed by 0257). The Desktop icon
also opened the console menu instead of the home page. A new window fixed everything: loading
the new file refreshed the shortcuts and the right-click entry (`_mh_refresh`). Nothing told the
maintainer that the loaded `mh` was out of date, so it looked like a broken build.

## Goal

When `mh` runs and its own file (`$MyInvocation.MyCommand.ScriptBlock.File`) has changed since
it was loaded, say in one line, before doing anything else: "mh.ps1 changed since this window loaded it:
type . "$HOME\media-hygiene\mh.ps1" (or open a new window)". Optionally reload it automatically
and run the command again. Decide which; a reload re-runs `_mh_refresh`, so it must stay quiet
when there is nothing to refresh.

## Acceptance

- Record the file's LastWriteTime (or a hash written into the file by `launcher`) at load time.
  Compare it on each `mh` call. The check must be cheap: one stat, no docker call.
- Do the same in mh.sh (WSL): the same trap applies with `source`.
- If the file was removed or moved, say nothing (the call still works from memory).
- Tests: the generated scripts contain the check (render tests). Add a step to
  `tests/measure/mh-measure.ps1` that loads mh.ps1, writes it again, then runs `mh version`
  and expects the line.
- Update the docs: the launcher page in both languages says that a new mh.ps1 needs reloading,
  or a new window.
