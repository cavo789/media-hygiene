# 0243 — `browse` opened from the home page: *Apply now* runs `clean --decisions`; the docs say a set-aside photo is remembered

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/search/app.py`, `src/media_hygiene/search/chosen_api.py`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/search/templates/browse.js.j2`, `src/media_hygiene/review/home_views.py`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/cli/cmd_browse.py`, `src/media_hygiene/cli/cmd_home.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/tags/test_browse_page.py`, `documentation/en/commands/browse.md`, `documentation/fr/commands/browse.md`

## Context

Follows 0223 (PARTIAL). Two of its items were waiting for other TODOs, now done:
- the *Apply now* button when the page is opened from the home page: the home page exists
  (0209, 0210: a step chosen there ends the page with `STEP_EXIT_BASE + step`, `mh` runs it,
  then opens the home page again; every page has "⌂ Home", `home_link.html.j2`);
- "remembered when it comes back": 0216 is done (`ActionKind.remembered`, `quarantine-chosen`
  included), so the browse page and docs can say it.
Decided by the maintainer (inbox, 2026-10-19): both.

## What to do

- When `browse` was opened from the home page (the same signal "⌂ Home" uses), and the
  selection saved under `chosen` is not empty: an *Apply now* button next to the saved line.
  It ends the page with the exit code of the home step that runs `clean --decisions` (reuse
  the step's number: no new code path in `mh`), so `mh` runs it with its usual question, then
  opens the home page again. Opened from `mh browse` directly: no button (the next step line
  stays).
- The saved line and `commands/browse.md`: "set aside — and remembered: if the photo comes back
  (a new copy from the phone), the audit proposes it again" — the wording 0216 used in its own
  docs; check it before copying.

## Acceptance

- Integration: opened from home with a choice → the button, its POST ends with the clean step's
  code; opened directly → no button; nothing chosen → no button.
- Docs both languages: `commands/browse.md`.

## Gain (estimated)

From the home page: choose, then one click to the quarantine, instead of going back home and
finding the clean step.
