# 0209 — `home`: a home page in the browser — where you are, the next step, every step, the reports

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_home.py` (new), `src/media_hygiene/cli/app.py`, `src/media_hygiene/cli/safety.py`, `src/media_hygiene/cli/menu_catalog.py`, `src/media_hygiene/cli/menu_steps.py`, `src/media_hygiene/cli/status_next.py`, `src/media_hygiene/services/home.py` (new), `src/media_hygiene/review/home_app.py` (new), `src/media_hygiene/review/home_views.py` (new), `src/media_hygiene/review/templates/home.html.j2` (new), `src/media_hygiene/review/templates/home.js.j2` (new), `src/media_hygiene/review/local_app.py`, `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/templates/near_review.html.j2`, `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_home_page.py` (new), `tests/support/docs/scenario.py`, `tests/support/docs/pages.py`, `.config/mkdocs/mkdocs.yml`, `documentation/en/commands/home.md` (new), `documentation/fr/commands/home.md` (new), `documentation/en/reference-commands.md`, `documentation/fr/reference-commands.md`

## Context

Chosen by the maintainer on 2026-10-17 (proposal F5: "a home page that replaces the numbered
menu"), after the competitor research's verdict on a GUI: no native window, no TUI, no second
codebase. The tool already has six pages served by one asyncio server (`services/reviewing.py`,
`review/local_app.py`: review, review --near, review-sort, places, search, people). What the
Windows audience lacks is one entry point in the browser instead of the numbered menu in
PowerShell (0172).

This TODO is the container side; 0210 makes `mh` and the shortcut open it and run the steps it
chooses; 0211 runs the audit inside the page.

## What to do

- `media-hygiene home`: a page command (`PAGE_COMMANDS` and `READ_ONLY_COMMANDS` in
  `cli/safety.py`: the photos stay `:ro`), served like the other pages, showing:
  - what `status` says (0063): the last audit, the quarantine, the runs that can be undone, the
    reviews not applied; the next step as a big button;
  - the steps of the three guides, from the same source as `mh menu` (`menu_catalog`,
    `menu_steps`), with their badges (🔒 ↩️ ⚠️, 🤖);
  - the reports (`index.html` and the latest report of each kind);
  - when an audit exists, a few previews of what it found (the cached previews).
- A step's button asks the server to end with the step's number: the process exits with code
  `100 + n`, `n` being the step's number in `mh menu`, and `mh` runs that step in the terminal
  with the mounts it needs (0210). A step the menu cannot fill (`album …`) shows the command to
  type.
- While no server answers on the port, the page polls and says "Running in the PowerShell window:
  this page comes back when it ends"; it reloads when a page answers again on the same port.
- Every other page gets a "⌂ Home" link: `POST /api/stop` in `LocalApp` ends its server with code
  0, and `mh` then opens the home page again (0210). Loopback `Host` only and JSON-only `POST`, as
  the other endpoints.
- A new verb (CLAUDE.md): its page in both languages, its name in `COMMANDS_TOO`
  (`tests/support/docs/scenario.py`) and in the mkdocs nav; a capture of the page (synthetic
  pictures).

## Explicit non-goals

- Running a command inside this container: the photos stay `:ro`, every action goes through `mh`,
  which mounts what each command needs. The audit's progress in the page is 0211.
- `mh` and the shortcut: 0210.

## Acceptance

- Integration (HTTP): the page's state matches `status` and `mh menu` on the same folders; a step's
  button ends the server with `100 + n`; `/api/stop` ends any page with 0; another `Host` is
  refused.
- Docs both languages; say in the report that `docs_screenshots` should run.

## Gain (estimated)

For a non-technical user: a numbered list in PowerShell → a page showing where they stand, the
next step as a button, and the photos found.

## Status — PARTIAL (2026-10-17)

### Done
- `media-hygiene home` (`cli/cmd_home.py`, `PAGE_COMMANDS`, `READ_ONLY_COMMANDS`): the state from
  the same sources as `status` and `mh menu` (`cli/home_state.py`, `cli/home_reports.py`): status
  lines, undo line, next step as a big button, every step numbered as `mh menu` with its badges,
  the latest audit/clean reports and `index.html` (served by the page itself under `/reports/`,
  `review/report_files.py`, never outside the folder), 8 thumbnails of the last audit's report.
- `POST /api/step {number, command}` ends the server with `100 + n` (checked against the menu
  read again: a stale page gets 409); the command exits with that code and names the step.
  The page then says "Running in the PowerShell window…" and reloads once the server was seen
  gone, then answering again.
- `review/ending.py`: every page server (`run_server`) answers `POST /api/stop` (loopback `Host`,
  JSON only) and ends with 0; every other page (review, near, pairs, junk, review-sort, places,
  search, browse, people) includes the shared `home_link.html.j2` ("⌂ Home"), found from any
  package through a `ChoiceLoader` in `i18n/templates.py`.
- Docs: `commands/home.md` (en, fr), reference tables, `--help` capture of `reference-commands`
  refreshed by hand, `COMMANDS_TOO`, mkdocs nav; French catalog.
- Tests: `tests/integration/test_home_page.py`; `home` added to `test_read_only_commands.py`.

### Not done
- A capture of the page (`images/home.webp`).
  **Reason:** `docs_screenshots` not run (heavy, needs asking): add a `home` mode to
  `tests/support/docs/browser.py` / `served.py`, run it, reference the image in both pages.
- `mh` reopening the home page after a step or a "⌂ Home" (the exit codes are in place).
  **Reason:** 0210 (launcher side), out of scope here.
