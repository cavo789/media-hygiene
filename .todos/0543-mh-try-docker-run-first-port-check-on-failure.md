# 0543 — mh: try `docker run` first, check the port only when Docker refuses it

- **Priority**: High
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh_guards.ps1.j2`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh_lan.ps1.j2`, `src/media_hygiene/cli/templates/mh_guards.sh.j2`, `src/media_hygiene/services/launcher_guards.py`, `src/media_hygiene/services/launcher_port.py`, `tests/unit/test_launcher_guards.py`, `tests/unit/test_launcher_port.py`, `tests/measure/mh-measure.ps1`, `documentation/en|fr/reference-troubleshooting.md`

## Reported (maintainer, 2026-10-30)

Before 0253 (2026-10-19), `mh` could be typed again right after the previous container
closed, without trouble. Since then, the port check refuses on "Idle (process 0)" almost
every time; once, `mh` had to be typed four times (no container running, checked in
Docker Desktop) before it started. 0503 now waits up to 10 s on PID 0, which may not be
enough and still adds a wait where none existed.

## Analysis (estimated, not measured)

The check (0253) reads `Get-NetTCPConnection` **before** starting Docker and believes it.
A `Listen` row owned by PID 0 is what Windows shows while a socket is being released, or
when the process that opened it exited and a child still holds an inherited handle. Before
0253, `docker run` was simply tried, and the maintainer's experience says it succeeded in
those moments: Docker could bind although Windows still showed the row.

## To do

- Drop the pre-start port check from the normal path: `mh` runs `docker run` as before 0253.
- Only when `docker run` fails with Docker's "port is already allocated" / "bind: … address
  already in use" error, run the diagnosis:
  - a real process holds the port (any PID but 0 and dead ones; PID 4 `System` included):
    the 0253 refusal, red, naming the program and the port, `[review] port` to change it;
  - PID 0 / dead PID: say one line ("Le port 8088 se libère encore…"), retry `docker run`
    every second up to the 0503 limit, then the red refusal without a process name.
- Keep 0503's behaviour in the home loop: a refused step reopens home, refusal said once.
- Keep the guards' order (a refusal never after a success line): the "Média Hygiène
  tourne" / LAN lines are printed once the container has started.
- `mh_guards.sh.j2`: same order (try first, diagnose on failure).
- Tests: rendered `mh.ps1` runs `docker run` before any `Get-NetTCPConnection`; the
  diagnosis is reached only on a bind error; PID 0 → retry loop; a real PID → refusal.
- `tests/measure/mh-measure.ps1` (step 42 of 0503): also record whether `docker run`
  succeeds while the PID 0 row is shown — the measurement that confirms this design.
- Docs (en + fr) troubleshooting line; `docs_screenshots` afterwards.

## Explicit NON-goals

- Serving pages inside the home server without restarting a container (0505/0506).
- Recording why a container stopped unexpectedly (separate TODO if wanted).

## Where the user gains

Before: `mh` typed right after a page closed is refused, or waits, sometimes four tries
in a row. After: it starts at once whenever Docker can bind (as before 2026-10-19); the
clear refusal of 0253 stays for a real program on the port.
