# 0661 — A running step is shown on every page: chip in the header, tab title, notification

- **Priority**: High
- **Batch**: one-interface
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/page_header.html.j2`, `src/media_hygiene/review/templates/shell_top.html.j2`, `src/media_hygiene/review/templates/home_notify.js.j2`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/step_watch.py`, `tests/unit/`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

The maintainer's wish (2026-11-10): stay in the web interface "like any application", with a
notification and a loader showing how far a step is, instead of looking at PowerShell.
The follow dialog exists on the **home page only** (0514, PARTIAL): `GET /api/step` gives the
stage, done / total and the file. *Measured* by `grep` over the templates (2026-11-10):
the browser `Notification` API is used in `home_notify.js.j2` only, no template sets
`document.title`, and no page but the home page shows that a step runs. A user who started an
audit and went to the library sees nothing of it until they come back home.

## Proposal

- A small chip in the shared header (`page_header.html.j2` / `shell_top.html.j2`), on every
  page of the home server: *⏳ Audit · 45 % · 3 min left*, fed by the same `GET /api/step`;
  a click opens the follow dialog (the home page's, shared). Nothing shown while idle.
- The tab title carries the progress while a step runs (`45 % · Audit — Media Hygiene`), so
  the tab bar is the loader when the user works elsewhere.
- At the end: a toast on the page shown (the summary's first line and the 👉 line), and the
  browser notification when the tab is hidden (the permission asked once, from the first
  step started, as today on the home page).
- One poll for the whole page (the chip, the dialog and *Apply now* share it), slowed down
  while the tab is hidden.
- A phone sees the chip read-only (no Stop).

## Acceptance

- [ ] The chip, the title and the end toast on every page extending `page_frame.html.j2`
      and on the home page; a test over the served pages (as `tests/unit/test_page_frame.py`)
- [ ] Checked in headless Chromium with a mocked `/api/step` (running → done), no `pageerror`
- [ ] Docs EN + FR; say that `docs_screenshots` should run

## Where the user gains

Before: the state of a long step is visible on 1 page (home) or in the console. After: on
every page, in the tab title and by a notification — no need to look at PowerShell to know
whether the audit ended.

## Status — PARTIAL (2026-11-11)

### Done

- `review/templates/step_chip.html.j2`, included once by the frame, the home page and the album
  page (not a shared link): the chip in the header's slot (`data-step-slot`), *⏳ Audit · 45 % ·
  3 min left*, hidden while idle; its click opens the home page's follow dialog
  (`mhStepOpen`) or a small read-only dialog elsewhere; the tab title carries the progress; the
  end said through `mhSay` and, tab hidden, the notification (`mhNotify`, the code moved from
  `home_notify.js.j2`).
- One poll per page (`mhStep.watch` / `claim`): the home page's dialog, its resume on load and
  *Apply now* follow it; 1 s while running, 5 s idle, 15 s hidden, none on a server without
  `/api/step` (404). Purge and shrink keep their own follow but claim the step (no double toast).
- A paired phone may `GET /api/step` (`lan_paths._HOME_READS`); its `POST` stays the PC's; no Stop.
- Tests: `tests/unit/test_step_chip.py`, `test_pick_pages` counts the chip, CI browser walk
  `tests/support/step_walk.py` (mocked running → done, no `pageerror`). Docs EN + FR (`home.md`).

### Not done

- The end message is *Done: <stage>.* / *Stopped (code n): <stage>.*: `/api/step` does not carry
  the step's summary first line nor its 👉 line. Needs the step to write them beside its
  progress (`services/step_progress.py`) and `read_state` to return them.
- The browser walk runs in CI only (no Playwright here): not run locally.
- `docs_screenshots` should run (header changed while a step runs; idle captures unchanged).
