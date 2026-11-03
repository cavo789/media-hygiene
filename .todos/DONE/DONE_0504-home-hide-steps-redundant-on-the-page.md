# 0504 — Home page: hide the steps the page already shows (folders, home, status, menu, open, reports)

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/cli/menu_entry.py`, `src/media_hygiene/cli/menu_catalog_tools.py`, `src/media_hygiene/cli/menu_catalog_settings.py`, `src/media_hygiene/cli/menu_catalog_clean.py`, `src/media_hygiene/review/templates/home_draw.js.j2`, `src/media_hygiene/review/home_texts.py`, `tests/unit/test_menu_catalog.py`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Reported (maintainer, 2026-10-30)

On `/#settings`, "See your folders" (`mh folders`) sends the user to PowerShell to read what
the sidebar's "Your folders (N)" panel (`home_draw.js.j2`, `#foldersSummary`) and the
"Your folders" group of Settings (`extra="folders"`) already show.

Same day, on `/#reports`: the page has an "All the reports" link (served at 127.0.0.1) and,
lower, "Read the reports in your browser" (`mh open`, the same `index.html` from `C:\...`).
Being on the web page, stay on the web: drop `mh open` there. "List the reports"
(`mh reports`) is useful in the console only: drop it from the page too.

## What the page repeats (read in the catalog, 2026-10-30)

| Step | Why it is useless on the page |
|---|---|
| `folders` (`menu_catalog_tools.py`) | the folder list is already on the page, twice |
| `home` (`menu_catalog_settings.py`) | opens the page the user is on |
| `status` | its own text: "the same summary as the home page" |
| `menu` | the same catalog, numbered, in the console |
| `open` (`menu_catalog_clean.py`, Kind.HOST) | the "All the reports" link of `/#reports` opens the same index, served |
| `reports` (`menu_catalog_tools.py`) | a console listing; the page's link already shows them all (its "write the index again" part: check the served index is always current, else keep a page action for it) |

`config` stays: the page does not say where each setting comes from (file / env / CLI).

## To do

1. A `Step` flag (e.g. `web: bool = True`): `False` hides the step on the home page, its
   palette and its search; `mh menu` and `mh --help` keep it (useful in the console).
2. Set it on the six steps above. `open` is also in the Clean guide's sequence
   (`menu_catalog_clean.py`, `guide = ("audit", "open", "clean", …)`): on the page that step
   becomes the "All the reports" link (or simply disappears) — the guide must not show a gap.
   The Reports area's group (`menu_catalog_tools.py`, `Group(_("The commands"), ("open",
   "reports", "reports-prune"))`) keeps only `reports-prune` on the page.
3. `mh folders` also says the state of the quarantines: check whether the folders panel
   shows it; if not, add it there (per drive, mounted or not) before hiding the step.
4. Tests: the six absent from the page's catalog, present in `mh menu`.
5. Docs EN + FR (home page): where the folders are seen. `docs_screenshots` should then
   run (Settings and Reports captures change) — not run by the TODO.
