# 0512 — A page opened by a typed command also offers "Back to the home page" and *Apply now*

- **Priority**: High
- **Batch**: launcher
- **Depends**: 0503 (the relaunch on the same port must not fail on "Idle (process 0)"), 0511
- **Files**: `src/media_hygiene/review/templates/page_header.html.j2`, `src/media_hygiene/review/templates/home_link.html.j2`, `src/media_hygiene/review/apply_api.py`, `src/media_hygiene/review/apply_relay.py`, `src/media_hygiene/services/review_serving.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/constants.py`, `tests/unit/`, `tests/measure/mh-measure.ps1`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`
- **Needs maintainer**: a run on Windows PowerShell 5.1 + Docker Desktop of the new path

## Reported (maintainer, 2026-10-30)

`mh review --intruders` typed in PowerShell: the page has no "Back to the home page" — "a
violation of our standards" (every page: the way back home at the same place). Same remark
the same day for *Apply now* (0511).

## Today (read, 2026-10-30)

Not a missing include: `page_frame.html.j2` includes `home_link.html.j2` on every page, and
`page_header.html.j2` shows `#homeLink` only when `header.shared` (served by the home server)
or `header.home` (`mh` opened the page from the home page). A typed command has no home
loop waiting behind it: the link would end the page and nothing would open home. *Apply now*
has the same condition (`apply_api.py`: "Opened by its command alone, nobody would run the
step: no button, and this route refuses."). So every page opened by a typed command lacks
both — by design, against the standard the maintainer expects.

## To do

1. `mh.ps1` / `mh.sh`: when a page started by a typed command ends with a new exit code
   ("go home", a named constant beside `STEP_EXIT_BASE`), `mh` starts the home page in the
   same window (waiting for the port as 0503 does). Likewise "apply then home": run `clean
   --decisions` with its usual question, then home.
2. Every page shows `#homeLink` and *Apply now* whenever it runs under `mh` (the launcher
   says so through the environment, as `relay` does today); only a bare `docker run` without
   `mh` keeps neither (nothing to come back to) — say there instead the command to type.
3. Tests: rendered headers with/without `mh`; the new exit code handled in the rendered
   `mh.ps1` (and `mh.sh`); a page typed then "Back to the home page" → home started.
4. `tests/measure/mh-measure.ps1`: a step typing `mh review --intruders`, clicking home
   through `/api/stop`, and recording whether home answers and how long it takes.
5. Docs EN + FR (launcher page); `docs_screenshots` should then run — not run by the TODO.

## Where the user gains

Before: a page opened from the console is a dead end (no way home, no Apply: Ctrl+C, type
`mh`, type `clean --decisions`). After: the same two buttons on every page, however it was
opened.
