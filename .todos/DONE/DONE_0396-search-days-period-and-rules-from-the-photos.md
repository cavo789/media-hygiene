# 0396 — search/browse: a period to the day (two calendars), and a rule created or updated from the photos it shows

- **Priority**: High
- **Batch**: search
- **Depends**: 0392, 0394
- **Files**: `src/media_hygiene/search/views.py`, `src/media_hygiene/search/query.py`, `src/media_hygiene/search/statements.py`, `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/review/sort_rule.py`, `src/media_hygiene/review/templates/sort_review_rule.js.j2`, `src/media_hygiene/review/templates/rule_dialog.html.j2`, `src/media_hygiene/classify/rules_file.py`, `src/media_hygiene/classify/rules_edit.py`, `src/media_hygiene/services/search_app.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`

## Why

Maintainer, 2026-10-25: writing a date rule blind is risky (the wedding of 0394 took 44
files, not 14). "Can we use the screen that shows the photos? I would type the period (5 to
6 August 2017), see the photos, and maybe correct it (only 5/08/2017) because I would see the
problems." Today the search page (`search`, the 🔎 tab of `browse`) filters by **year** only
(`SearchAsked.year_from`/`year_to`, `Filters.years`): "From year … To year".

## What

Load the skill `photo-picking-pages` first (the page is a page of photos to pick).

- **A period to the day**: "From year / To year" becomes two real calendars (`<input
  type="date">`, the browser's own date picker, Windows-first), a day each; one day alone is a
  period of one day; a year typed alone still works (1 January to 31 December). The query
  filters on the day the photo was taken (the index's date, as `classify` dates it),
  both days included; `found_by` writes `2017-08-05..2017-08-06`.
- **Create a rule from the period**: a button *📌 Make it a rule* (shown once a period is
  set) opens the same dialog as review-sort's *Remember as a rule* (0392), moved to a shared
  template (`review/templates/rule_dialog.html.j2` + its script), prefilled with the period;
  name and folder typed there, `keep_folders` on.
- **Update a rule**: in the same dialog, *Update the rule…* lists the `date_range` rules of
  `config.toml` (sorted as 0395: latest first); choosing one fills the dialog with it and
  saving replaces it in place (`rules_edit.replace_rule`).
- **What the rule would take, shown as photos**: the dialog's preview (0392's counts)
  also *shows* the photos: the grid of the page is narrowed to the files the rule would take
  (an event is taken when at least half of its files fall on the days, a file of no event
  by its own date: as `classify` reads it), each with where it would go
  ("→ 2017/Fêtes/Mariages/Mariage d'Hervé et Magda"), the files of the period the rule would
  *not* take marked too (a screenshot left to its own rule, 0394). The destinations come from
  the classify engine run on those files only, with the settings and the rule typed (a dry
  run: nothing written); measure its time on the maintainer's index (52,094 files): it must
  answer in under 2 s for a period of a few days, or say "computing…".
- Without a classify run (no `plan.json` to read events from): the dialog says so, with the
  command.

## Tests

The day filter (both bounds included, one day alone, a year alone); a rule created from a
period, written and read back; a rule updated in place; the preview's photos and destinations
against the engine for the wedding case of 0394; the page in `test_pick_pages.py`, its gestures
in headless Chromium (skill checklist); say that `docs_screenshots` should run.
