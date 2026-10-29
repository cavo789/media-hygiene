# 0476 — Import a period only: today, this week, this month, since the last import

- **Priority**: Medium
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_import.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/services/launcher_phone_end.py`, `src/media_hygiene/review/templates/` (home page)

## Why

The maintainer, 2026-10-29: plug the phone, import only today's (or this week's) photos, then
the slideshow is ready minutes later (0475). Today `import` has no period option; it already
skips files held or set aside on purpose (0377), so a period mostly saves time and lets the
user pick (a weekend only, older unimported photos left).

## Decided (2026-10-29, the maintainer: "go for your proposals")

- CLI: `mh import [--phone] --since today|week|month|all|<YYYY-MM-DD>`.
- Home page: *Today · This week · This month · All* before starting (the same buttons as search's dates).
- Default with no option: **since the last import** (its date kept by `mh`); the first import takes all.
- Date of a file: the date in its name when there is one (`20261029_…`, `IMG_20261029…`,
  `Screenshot_2026…`, `VID_…`), else its modified time on the phone; no EXIF read over USB
  (too slow, estimated). For `--phone` the filter runs in PowerShell (`mh.ps1`, Windows
  PowerShell 5.1) before the copy.
- The summary says what was left: « 1 240 older photos left on the phone ».

## Acceptance

- Unit tests of the name → date rules (each pattern, none → mtime); `--since week` copies only
  the files of the last 7 days (synthetic folder); the last-import date is saved and read back.
- A step in `tests/measure/mh-measure.ps1` for the phone path (only the maintainer can run it).

## Status (2026-10-29): PARTIAL

Done: `mh import [--phone] --since today|week|month|all|<YYYY-MM-DD>`
(`services/import_since.py`: the day in the name — `20261029_…`, `IMG_/VID_/PXL_…`,
`Screenshot_2026-10-29…` — else the modified time; an unknown day is kept). Phone: no
`--since` = since the last import, its day written by `mh.ps1` into the journal folder
(`last-import.txt`) after an import that copied files; the first import takes all. The new
files before the period become case `older` in `phone-plan` and are counted: « Left on the
phone: 1,240 older photos and videos ». Folder import: `--since` filters the plan; its default
stays every file (deviation: a NAS holds years never imported). Step 38 of `mh-measure.ps1`.
Tests: `tests/unit/test_import_since.py`, `test_launcher_phone.py`. Docs EN+FR (import).

Deviation: the period is decided in the container (`phone-plan`, before any copy) rather than
in PowerShell: one set of rules, unit-tested, no extra cost (the listing is piped there anyway).

Remaining:
- Home page: *Today · This week · This month · All* before starting the phone import.
