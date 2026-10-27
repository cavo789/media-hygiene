# 0368 — The home page says when `mh` is older than its image

- **Priority**: Low
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/services/launcher_stamp.py`, `src/media_hygiene/review/home_parts.py`, `src/media_hygiene/review/home_texts.py`, `src/media_hygiene/review/templates/home.html.j2`, `tests/integration/test_home_page.py`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Context

Review of the feedback of 2026-10-21 (0290, maintainer 2026-10-25: *a TODO*). Since 0290, `mh`
says at the first call when its file is older than its image (`launcher_stamp.py`), fixed by
`mh update`. The line is printed in the console only; the home page opened from a shortcut runs
in a minimised window, so the line is never seen.

## What to do

1. `mh` passes the stamp of its file to the home server (the same comparison as 0290, no second
   rule); the page shows one banner at the top: the line of the console and `mh update` to copy.
2. No banner when the stamps match or `mh` gives none (an older `mh`).
3. Tests: a stamp older → banner with `mh update`; equal or absent → none. Docs en + fr
   (`commands/home.md`).

## Acceptance

- A home page opened by an `mh` older than its image shows the banner; after `mh update`, none.

## Gain

The line seen by the user who only uses the home page: 0 → 1 (estimated: the console is minimised).

## Decided (2026-10-27)

Review of the `/todo:iterate` of 2026-10-26 (0338 item 3, maintainer): the home page offers
`mh update` **as a button** when `mh` is older than its image, not only a line. The page's server
must first receive the launcher's stamp (it does not today: 0338's report).
