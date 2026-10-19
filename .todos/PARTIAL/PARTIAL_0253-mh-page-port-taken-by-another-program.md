# 0253 — `mh`: port 8088 taken by another program — say which, never Docker's raw error

- **Priority**: Low — rare (another local server on 8088); the troubleshooting page covers it today
- **Batch**: launcher
- **Depends**: 0250
- **Files**: `src/media_hygiene/cli/templates/mh_guards.ps1.j2`, `src/media_hygiene/cli/templates/mh_guards.sh.j2`, `src/media_hygiene/services/launcher_guards.py`, `documentation/en/reference-troubleshooting.md`, `documentation/fr/reference-troubleshooting.md`, `tests/unit/test_launcher_guards.py`, `tests/measure/mh-measure.ps1`

## Context

0250 frees the page port when a container left by a closed window holds it (`docker ps
--filter publish=8088`). A program that is not a container (another local server, an IDE
preview) still makes `docker run -p 127.0.0.1:8088:8088` fail with Docker's raw "port is
already allocated" / "bind: address already in use". Maintainer's choice (inbox 2026-10-19):
tell it apart rather than leave it to the troubleshooting page.

## What to do

1. In the guard, after the container check of 0250 and only when no container holds the port:
   probe the port.
   - PowerShell 5.1: `Get-NetTCPConnection -LocalPort 8088 -State Listen -ErrorAction
     SilentlyContinue` → `OwningProcess` → `Get-Process -Id` for its name. No `Add-Type`
     (Avast), ASCII only.
   - bash: `ss -ltnp 'sport = :8088'` when present, else skip the probe (no new dependency).
   Docker Desktop's own backend (`com.docker.backend` / `wslrelay`) listens for published
   ports: a listener of these names is not "another program" (to check on Windows which name
   holds a published port).
2. Another program found: one line naming it and its PID, the tip to close it or to use
   another port (`--port` + the same `-p`, if `mh` can pass it; else say so); nothing runs.
3. The probe's cost before each page: measure on Windows (step 10 of `mh-measure.ps1`, a
   `Start-Job` listener on 8088 → the line said); estimated 0.1–0.5 s (a CIM query).
4. Tests: rendered PowerShell text (ASCII, no Add-Type); bash with a fake `ss`. Docs en + fr:
   the troubleshooting entry says what `mh` now shows.

## Acceptance

- A non-Docker listener on 8088: `mh review` says its name and PID in one line, never
  Docker's raw error; a container case behaves as in 0250.

## Status — PARTIAL (2026-10-19)

### Done
- `mh.ps1` (`mh_guards.ps1.j2`, end of `_mh_page_free`): once no container holds the port,
  `Get-NetTCPConnection -LocalPort 8088 -State Listen` then `Get-Process -Id` name the listener;
  one line (*The port of the mh pages is used by another program, {name} (process {process}):
  close it, then type the command again. mh always uses this port.*), nothing runs. No
  `Add-Type`, ASCII. Docker's own listeners (`com.docker.backend`, `com.docker.proxy`,
  `wslrelay`, `vpnkit`, `docker-proxy`, `rootlesskit`, `dockerd`: `DOCKER_LISTENERS` in
  `services/launcher_guards.py`) are never "another program".
- `mh.sh` (`_mh_port_user`): `ss -ltnp 'sport = :8088'` when `ss` exists; it names only the
  user's own programs, so a listener without a name (another user's, root's) or no `ss` lets
  Docker say it, as before (no new dependency).
- `--port`: `mh` publishes a fixed `-p 127.0.0.1:8088:8088`, so the line says mh always uses
  this port; the troubleshooting page keeps `-p` + `--port` for `docker run` typed by hand.
- Tests: `tests/unit/test_launcher_guards.py` (bash with a fake `ss`: another program named and
  nothing run, Docker's listener and a nameless one let through, no probe before an audit;
  the rendered PowerShell). Docs en + fr: troubleshooting, *The review page does not open*.

### Not done
- Step 10f of `tests/measure/mh-measure.ps1`: which name Windows gives the listener of a port a
  container publishes (to confirm `DOCKER_LISTENERS`), the line `mh review` says with another
  program on 8088, and the probe's time (estimated 0.1-0.5 s, a CIM query).
  **Reason:** Windows + Docker Desktop only. Command (PowerShell 5.1):
  `Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/COMMIT/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1`,
  `Unblock-File .\mh-measure.ps1`, then `.\mh-measure.ps1 -Only 10 -Count 20`.
