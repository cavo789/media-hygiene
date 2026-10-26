# 0363 — *Apply now* runs its step beside the home server, without `mh menu`

- **Priority**: High
- **Batch**: home
- **Depends**: 0355
- **Files**: `src/media_hygiene/review/apply_api.py`, `src/media_hygiene/services/search_app.py`, `src/media_hygiene/services/home_pages.py`, `src/media_hygiene/services/review_serving.py`, `src/media_hygiene/review/templates/apply_now.html.j2`, `tests/integration/test_review_apply.py`, `tests/integration/tags/test_browse_page.py`

## Context

Review of the feedback of 2026-10-24 (maintainer, 2026-10-25: *a TODO of its own now*). Since
0354/0355 a step chosen on the home page reaches `mh` through the one-shot files, and a console
step runs while the home server stays up. *Apply now* (browse, and the reviews opened from the
home page, 0243/0288) still ends its server with `STEP_EXIT_BASE + n` (`apply_api.py`,
`ApplyDesk.answer`): `mh` then runs `mh menu` in a container of its own to learn step `n`
(2.1–2.5 s, *measured*, step 35b of `mh-measure.ps1`), and on browse — served by the home server
since 0356 — the whole home server ends too.

## What to do

1. `ApplyDesk` gets the reports folder and whether `mh` keeps the server up (`step_watch`):
   - kept up (`MEDIA_HYGIENE_LAUNCHER_STEPS=3`): `keep_step` with the words of
     `clean --decisions` (the apply step's command without `mh`): the server stays up, the page
     follows the step (`GET /api/step`, as `home_run.js.j2` does since 0355), then reads its
     state again (the files set aside are gone from the decisions);
   - an `mh` that reads the one-shot file (`2`): the words in `.mh-step.json`, the fields code;
   - else the number, as today.
2. `apply_now.html.j2`: a kept step shows *runs in the window of mh … this page stays open*,
   then *done* / *stopped (code n)*; never *This page is closed*.
3. The reviews still served by a container of their own (until 0357) end as today with the
   words in the file (no `mh menu`).
4. Tests: browse served by the home server: *Apply now* writes `.mh-step-now.json` with
   `clean --decisions`, the server does not end; a review of its own: the one-shot file and the
   fields code; an older `mh`: the number.

## Acceptance

- *Apply now* from browse: `clean --decisions` runs in the window of mh, the page stays open and
  shows the result; no `mh menu` container (Docker's events, step 36 of `mh-measure.ps1`).

## Gain

*Apply now*: 2.1–2.5 s of `mh menu` less (*measured*, 35b), and on browse no restart of the home
server (4.8–5.6 s, *measured*, 35d).

## Outcome (2026-10-26)

DONE. `review/apply_relay.py`: browse on the home server with `mh` keeping it up
(`3`) → `keep_step` (`.mh-step-now.json`, `clean --decisions`), the page follows
`GET /api/step` (`follow` in the answer), says *Done* / *Stopped (code n)*, reloads; a
page of its own (reviews, people, `mh browse`) with `2`/`3` → `.mh-step.json` + fields
code; older `mh` or unwritable folder → the number. `APPLY_PATH` moved to `home_views`,
`STEP_PATH` to `step_watch` (import cycles). Acceptance on Windows (step 36 of
`mh-measure.ps1`, Docker events) still waits for the maintainer.
