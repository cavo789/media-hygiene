# 0211 — The home page runs the audit itself, its progress shown in the page

- **Priority**: Low
- **Batch**: home
- **Depends**: 0209
- **Files**: `src/media_hygiene/services/home.py`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/review/home_views.py`, `src/media_hygiene/review/templates/home.html.j2`, `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/console/progress.py`, `src/media_hygiene/console/page_progress.py` (new), `src/media_hygiene/services/audit.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_home_audit.py` (new), `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Context

Chosen by the maintainer on 2026-10-17 (proposal F5, its third stage). With 0209 and 0210, every
step of the home page runs in the PowerShell window, the audit included: the user is sent from the
browser to the terminal to watch its progress. The audit only reads the photos, so it can run
inside the home page's own container, whose photos are mounted `:ro`.

## What to do

- From the home page, `audit` runs in the home container (same settings and folders as
  `mh audit`), its progress shown in the page: each step of `Time per step` with its counts,
  polled through a JSON endpoint fed by a progress sink of the page (`console/page_progress.py`,
  next to the Rich one); at the end, the summary (the *What you can do* block), the report's link,
  and the home page refreshed.
- One audit at a time; the steps that act (clean, sort, undo, purge, album, xmp) are still relayed
  to `mh` (0210).
- Stopping (⌂, closing the tab, Ctrl+C in the terminal) ends the audit cleanly: the index keeps
  what it committed (0143), as with Ctrl+C today.

## Explicit non-goals

- Acting commands in the page: they need write mounts.
- Other long read-only commands (`tags`, `people`, `classify`): later, the same way, if wanted.

## Acceptance

- Integration: an audit started from the page gives the same findings as `audit` on the same
  folders; the progress endpoint reports the steps in order; a second start while one runs is
  refused; a stop leaves an index the next audit reuses.
- Docs both languages: the home command page.

## Gain (estimated)

The first audit no longer sends the user to the PowerShell window: the whole read-only part of the
guide happens in the browser.

## Status — PARTIAL (2026-10-17)

### Done
- **Audit now** on the home page runs the audit in a worker thread of the home container
  (`services/home_audit.py`, `cli/home_audit.py`): same checks, settings, report and *What you
  can do* actions as `audit` (`cli/audit_actions.action_list`, shared with `show_actions`).
- `console/page_progress.py`: a `ProgressSink` recording each step (title, hint, counts,
  finished) for `GET /api/audit`; `POST /api/audit {"action": "start"|"stop"}`; a second start
  while one runs gets 409. At the end: the audit's figures, the actions, the report's link, and
  the home page refreshed.
- Stop (button, Ctrl+C, or the server ending for a step): raised at the next progress report,
  between two files; the index keeps what it committed; an unexpected error says one line.
- Tests: `tests/integration/test_home_audit.py` (same summary as `audit`, steps in order, one
  at a time, stop then a full audit, failure, routes). Docs: the home command page (en, fr).

### Not done
- Stopping the audit when the browser tab is closed.
  **Reason:** needs a heartbeat from the page (the server cannot see a closed tab); the audit
  goes on until its end, Ctrl+C or the stop button. Worth a small follow-up if wanted.
- The `Time per step` durations (only counts are shown).
  **Reason:** the stopwatch's stage times are only known at the end; showing them after the
  run is a small follow-up.

## Inbox (2026-10-19)

- `Time per step` at the end → refiled as 0241.
- Stopping the audit when the tab is closed: dropped (maintainer).
