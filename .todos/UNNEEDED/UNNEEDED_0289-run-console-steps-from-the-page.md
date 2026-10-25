# 0289 — Consider running the console steps from the page itself (an API), starting with applying choices

- **Priority**: low
- **Batch**: home
- **Depends**: 0288
- **Files**: TBD (design first) — likely src/media_hygiene/review/home_app.py, src/media_hygiene/services/clean* , src/media_hygiene/review/templates/home_run.js.j2, src/media_hygiene/cli/templates/mh_menu.ps1.j2
- **Needs maintainer**: review of the design note (.claude/plans/0289-console-steps-from-the-page.md), then the follow-up TODOs are filed

## Context

Today a page can save choices but never touches a photo: every step that writes (`clean
--decisions`, `undo`, `purge`, `sort`…) ends the page and runs in the PowerShell window, which
asks its question there (0210, 0243, 0288). The maintainer wants a stronger web experience
(2026-10-21): apply from the page, without switching to PowerShell — and, later, drive
media-hygiene from a smartphone (0269), where there is no console at all.

A precedent exists: the audit already runs inside the home server (`POST /api/audit`, progress
in the page, one at a time, stop button — `home_app.py`).

## To study (a design note before any code)

- Which steps first: applying choices (`clean --tier near --decisions`) is the natural pilot;
  then `clean`, `undo`, `purge`, `sort`. List each step's console questions and refusals.
- Safety moves into the page: the confirmation (what will move, how many, where), the refusals
  `clean` has today (no persistent `/journal`, `:ro` data mounts, a drive quarantine not
  mounted) shown as page errors, never a traceback; the undo line at the end; a save proven
  by reading it back (journal read from disk).
- Mounts: a page opened from `mh` alone may not have the write mounts the step needs (`mh`
  mounts per command; `:ro` for read-only pages). What the home container must mount for this,
  and what that loses (a read-only page can no longer write by accident).
- One run at a time, Ctrl+C / tab closed mid-run (the journal's `pending`), progress and
  cancel like the audit's.
- The phone (0269): same API, but a request not from loopback — authentication, CSRF; keep it
  out of this TODO, but do not design anything that blocks it.
- What stays in the console (and why), so the page and the console never disagree.

## Acceptance

- [ ] A design note (`.claude/plans/` or this TODO) answering the points above, with what the
      change loses, reviewed with the maintainer before code.
- [ ] Then a follow-up TODO per lot (pilot: apply choices from the burst page via an API).

## Decided (2026-10-21)

By the maintainer (`/todo:iterate`): an unattended run writes the design note only
(`.claude/plans/0289-console-steps-from-the-page.md`), no code; the maintainer reviews it, then
the follow-up TODOs are filed.

Design note written (2026-10-21): .claude/plans/0289-console-steps-from-the-page.md

## Closed — superseded (2026-10-25, review of the feedback of 2026-10-21)

The six questions of the design note are answered by the single-server work: the server never
has the photos read-write, a page's write runs as a step of `mh` in its window, followed live
(0355, 0361, 0363); what is final is confirmed in the window of `mh` (0361 point 3); the phone
acts through 0360. The note stays in `.claude/plans/0289-console-steps-from-the-page.md`.
