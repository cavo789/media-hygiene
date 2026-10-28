# 0451 — `mh import --phone` audits the files it copied, in the open home page if any

- **Priority**: High
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/services/launcher_phone.py`, `src/media_hygiene/services/launcher_phone_end.py`, `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/cli/templates/mh_phone_free.ps1.j2`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/search/templates/search.html.j2`, `documentation/en/commands/import.md`, `documentation/fr/commands/import.md`

## Why

The maintainer, 2026-10-28, after `mh import --phone` (83 files copied):

1. *Set aside before on purpose, not copied: 164.* read as part of the 83: it counts the
   files of the phone (same name and size as a content set aside by `clean` or a review),
   but the line never says so.
2. *👉 What next: mh audit* left them unsure whether to wait or to type it; they wanted the
   web page to show the audit by itself. Meanwhile `mh search` did not find the photos of
   the day: they join the index only through an audit.
3. On the search page, the open tree *In a folder* was taller than the window, with no
   scroll bar: `#toc { flex: none; }` stopped the left column's list from shrinking.

## What (done)

- The set-aside line: *Also on the phone, skipped: {count} you set aside earlier (a clean or
  a review); they do not come back into your library.*
- After a copy (with or without `--free`), `_mh_phone_audit`: `POST /api/audit`
  `{"action": "start"}` to the home page on the pages' port, as its own button does; on any
  failure (no page, another page on the port, an audit already running), `mh audit` in the
  console.
- The home page looks for an audit every `IDLE_MS` (3 s) between runs: one started from the
  console brings it back to its home view, scrolled to the audit, followed, then reloaded on
  its summary. Between runs, a poll nobody answers is not *the page stopped* (a step may
  hold the server).
- Search: `#toc { flex: 0 1 auto; }`; a test that no framed page stops `#toc` shrinking.

## Left

- Measured on the maintainer's PC only: the page following an audit started by the import.
- `docs_screenshots` should run (the import's console output changed).
