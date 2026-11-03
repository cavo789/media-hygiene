# 0583 — Opening a page from another page waits for port 8088, then gives up

- **Priority**: Critical
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/services/launcher_port.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, the home page's step runner (`review/templates/home_run.js.j2`)

## Asked (maintainer, 2026-11-03)

From the home page, starting `mh people` now takes "an eternity", where it was quick a few
days ago. The console of `mh` shows, twice:

```text
La prochaine fois, tapez-la directement : mh people
Le port 8088 des pages de mh se libère encore (une page mh vient de s'arrêter) : quelques secondes d'attente...
Windows n'a pas encore libéré le port 8088 des pages de mh : attendez quelques secondes, puis retapez la commande ; ou choisissez un autre port, [review] port dans config.toml, puis mh update.
```

then the PowerShell prompt: the page never opens.

## Known — follow-up of 0503

- 0503 (`DONE/DONE_0503-mh-port-check-idle-false-alarm-and-red-error.md`, commit 37a46b63)
  met this very path on 2026-10-30: a page step chosen on the home page ends the home
  container, then `mh` starts the step's container at once on the same port, while Windows
  still shows the socket under PID 0. Its fix: wait for the release (`launcher_port`, poll
  every `PORT_POLL_MILLISECONDS` for `PORT_RELEASE_SECONDS` = 10 s), then refuse in red.
- Now the wait itself is the problem: the port is not released within 10 s, twice, then the
  refusal — every page step from the home page is slow or lost. Before 0503 the same click
  was quick most of the time (it failed only when the release was slow).
- So the hand-over should not depend on Windows releasing the port: reuse the running home
  server for the step's page (0417), keep the published port across steps, or bind the next
  container before the previous one is gone — never wait longer.

## To find (first)

- Why the port stays held: the home server's container still running or its socket not closed
  (no `SO_REUSEADDR`?), Docker Desktop's proxy (`com.docker.backend`/`wslrelay`) keeping the
  published port a while after `docker run` ends, or the next container started before the
  previous one exited.
- Why it was fast before 0503: did the old path reuse the running server (serve `people` from
  the home server, 0417) instead of a new container on the same port?

## Acceptance

- From the home page, `mh people` (and every page step) opens in a few seconds, as before 0503.
- A test reproduces the hand-over (server stopped, next one bound at once) on the code path.
- Measured on the maintainer's PC (a step of `tests/measure/mh-measure.ps1`): time from the
  click to the page shown, before → after.

## Status — PARTIAL (2026-11-03)

### Done

- Cause found (read from the code, not measured): a page step ends the home container, and
  `_mh_watch` returned as soon as `docker wait` said its process exited; `mh people` then ran
  `docker run -p 8088` while Docker (`--rm`) was still removing the container, which is when
  Docker Desktop drops its published port. Docker refused, and since 0543 every refusal with no
  non-Docker listener reads as "being released": retried each second, 10 s, refused; the home
  loop then started home again on the same race (the line said twice). Before 0543 the first
  try was delayed by the port read itself.
- `_mh_watch` (PowerShell and bash): once the server ended, `docker container inspect` every
  `CONTAINER_GONE_POLL_MILLISECONDS` (100) up to `CONTAINER_GONE_TRIES` (50, 5 s) until the
  container is gone, then the step's page starts (`launcher_port`, `PortGuard.gone_*`).
- Test: the bash `mh` run for real, the fake container still there for two checks: the page
  starts only after them (`test_a_page_step_binds_once_the_home_container_is_gone`).
- `tests/measure/mh-measure.ps1` step 43: seconds to bind 8088 at once vs once removed.

### Not done

- Measured click → page on Windows, before → after. **Reason:** Windows + Docker Desktop only
  (`-Only 43`). If removal is not what frees the port there, the next step is 0505/0506 (serve
  the page from the home server) or a published port kept across steps.

## Measured (maintainer, 2026-11-03 18:10, step 43, image 32cafce7)

Port 8088 bound in 0.9 s **in both cases** (3 runs each): started at once after the first
container ended, or once Docker removed it (removal 0.4 s). The race this TODO's fix assumed is
**not reproduced** by the script: the wait added by the fix costs ≈ 0.4 s and gains nothing
measured here. The real cause of the "eternity" stays to be found from a real click on
`mh people` from the home page (console lines + time), with the image of this branch.
