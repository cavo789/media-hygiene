# 0355 — The home server stays up while `mh` runs the steps asked on its page

- **Priority**: High
- **Batch**: home
- **Depends**: 0354
- **Files**: `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/review/home_step.py`, `src/media_hygiene/review/home_fields.py`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/services/home.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `tests/unit/test_launcher_home.py`, `tests/integration/test_home_page.py`, `tests/measure/mh-measure.ps1`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`
- **Needs maintainer**: one run of the new measure step on Windows (PowerShell 5.1 cannot be run in the devcontainer), to finish

## Context

Phase 1 of the single server (decided by the maintainer, 2026-10-24: "a single server pleases me
more"; read-only pages first, ready for the pages that write). Today the home server **ends** to
hand a step over: `mh` runs the step in the foreground, then starts the home page again (one
container, the state read again: 4.8–5.6 s back on the home page, *measured*, step 35d of
`mh-measure.ps1`, 0354). This is the base of everything after: the server must stay up while a
step runs in its own container.

The rule kept for good: **the server never gets the photos read-write**. A step that changes
photos runs in a container of its own, launched by `mh` with its own mounts and its write-ahead
journal (`undo`), whatever page asked for it. The server is never given Docker's socket (it would
control all of Docker Desktop).

## What to do

1. **`mh` starts the home server in the background** (`docker run -d`, its id kept, the
   page's port published as today), then waits in a loop:
   - the one-shot file `.mh-step.json` (the channel of 0266/0354, in the reports folder) appears:
     `mh` reads and removes it, writes `.mh-step-running.json` (words, start time), runs the step
     in the foreground of its window (its questions there, as today), then writes
     `.mh-step-done.json` (words, exit code, end time) and removes the running file;
   - the server's container ended (quit on the page, its tab closed, a crash): `mh` reads its
     exit code (`docker wait` started once with `Start-Process -PassThru`, `HasExited` checked at
     no cost; bash: `docker wait` in the background, `wait -n`) and ends the loop as today
     (`PAGE_CLOSED`, signals) — **a crash restarts it** once, said in one line;
   - Ctrl+C in `mh`'s window: the server stopped in `finally` (`docker stop`), the prompt back.
   - Polling the file: every 250 ms (`Test-Path`, a few ms; *estimated*). No `docker` call per
     poll (each one costs 0.1–0.2 s, *estimated* from 35a).
2. **The server keeps serving during a console step** (`clean`, `status`, `sort`…): `/api/step`
   writes the file and answers, no `ending.end` (a new value of `MEDIA_HYGIENE_LAUNCHER_STEPS`,
   e.g. `3`, says `mh` keeps it up; `2` and `1` keep today's ending for an older `mh.ps1`). A
   second step asked while one runs (a file, or the running file, present): 409 *A step is
   running in the window of mh*.
3. **The page follows the step**: `GET /api/step` says idle / running (words, since) / done
   (exit code); the dialog of `home_run.js.j2` says *running in the window of mh*, then the state
   is read again and the page refreshed in place when it is done — no reload, no waiting for a
   server.
4. **A page step** (search, browse, review…) still needs the port in this phase: the server ends
   as today (its words in the file), `mh` runs the page, then starts the server again in the
   background. 0356 removes this for the pages it serves.
5. The home page's own audit (`POST /api/audit`) is unchanged (it already runs in the server).
6. Old `mh.ps1` with a new image, new `mh.ps1` with an old image: both work (the variable says
   which protocol); `mh update` brings the new loop, said by the stale line (0290).
7. Tests: the bash loop with the fake docker of `test_launcher_home.py` (a console step runs while
   the server is up, the done file written, a crash restarted once, Ctrl+C stops it); the
   PowerShell template's blocks checked as text; the server's `/api/step` protocol (idle, running,
   done, 409). A measure step in `mh-measure.ps1`: a console step from the page, the home page
   still there during and after it (timed with Docker's events, as step 35d).
8. Docs en + fr (`commands/home.md`): the page stays open while a step runs in the window of mh.

## Acceptance

- After a console step chosen on the page, the home page is up to date without any reload or
  wait (measured: under 0.5 s after the step's end, against 4.8–5.6 s).
- Quit, a closed tab, Ctrl+C and a crash end or restart as said; never two servers on the port.

## Gain

Back on the home page after a console step: 4.8–5.6 s → under 0.5 s (*estimated*); the base for
0356 (pages served by the same server) and 0361 (pages that write).

## Status — PARTIAL (2026-10-24)

### Done
- `MEDIA_HYGIENE_LAUNCHER_STEPS=3` (`review/step_watch.py`, `WATCH`): a console step chosen on
  the page (numbered or with fields) is written into `.mh-step-now.json` with an id and the
  server keeps serving; a page step still ends it (`.mh-step.json`, 0354); any step asked while
  one waits or runs: 409 *A step is running in the window of mh*. `GET /api/step`: idle /
  waiting / running / done (id, exit code; a byte order mark accepted).
- `mh.ps1` / `mh.sh`: `_mh_watch` starts the home page with `docker run -d --cidfile`, sees its
  end through `docker wait` in a process of its own (PowerShell: `Start-Process -PassThru`,
  `HasExited`; bash: a background job), polls the file every 250 ms with no docker call, runs
  the step in its window, writes the running then done files (no byte order mark), stops the
  server on Ctrl+C (`finally` / `trap INT`), releases the tab job, the USB stick and the NAS
  volumes once the server ended. Older `mh` scripts keep today's protocol (values 1 and 2).
- The page (`home_run.js.j2`): a kept step shows *runs in the window of mh … This page stays
  open*, follows `GET /api/step`, then *done* / *stopped (code n)* and its state read again
  without reload; beats go on (not *away*).
- Tests: the bash loop with a fake docker that runs detached and asks console steps
  (`test_launcher_home.py`), the PowerShell blocks as text, the server's protocol
  (`test_step_watch.py`). Step 36 of `mh-measure.ps1`; docs en + fr (`commands/home.md`).

### Not done
- A crash of the server restarted once by `mh` (item 1 of *What to do*).
  **Reason:** an exit code that is not a step's, 0 or a signal's is today returned to the
  prompt; telling a crash from an exit of the tool (1 for a user error) needs a code of its own
  from the server — left for 0356, which changes how the server starts.
- The run on Windows: step 36 of `mh-measure.ps1` (PowerShell 5.1 cannot run in the
  devcontainer). Command: build the image of branch `iterate/2026-10-24`, then
  `.\mh-measure.ps1 -Only 36 -Count 1 -Image media-hygiene` (the script fetched by the commit
  of this branch, `mh update` first).
  **Reason:** only the maintainer's PC runs Windows PowerShell and Docker Desktop.

## Validated on Windows (2026-10-25, maintainer, by hand)

The image of `iterate/2026-10-24` and its `mh.ps1` (`mh update`): `mh` alone opens the home page;
search shows at once and the way back needs no F5 (step 35's timing by two Enters dropped as
meaningless now: real timings in the browser test of 0366); a console step chosen on the page
(*See what each run did*, `mh history`) runs in the PowerShell window while the home page stays
open; Quit, then `mh` again, works. The crash restart left by 0355 is TODO 0365.
