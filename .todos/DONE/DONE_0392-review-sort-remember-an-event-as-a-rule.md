# 0392 — review-sort: "Remember as a rule" writes a `date_range` rule from the event shown

- **Priority**: High
- **Batch**: review-sort
- **Depends**: 0387, 0391
- **Files**: `src/media_hygiene/review/sort_rule.py`, `src/media_hygiene/review/sort_app.py`, `src/media_hygiene/review/sort_choices.py`, `src/media_hygiene/review/sort_views.py`, `src/media_hygiene/review/templates/sort_review.html.j2`, `src/media_hygiene/classify/rules_file.py`, `src/media_hygiene/places/toml_edit.py`, `src/media_hygiene/services/sort_reviewing.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/sort/11-name-events-in-the-browser.md`, `documentation/fr/sort/11-name-events-in-the-browser.md`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`

## Why

Maintainer, 2026-10-25: "the events page is a good entry point to define date ranges and
validate them". Today a choice on the page holds for this plan only (carried over by
`classify`); a rule holds for every later run, the photos added later included (a new copy
from the phone, the daughters' folders). Searching `config.toml` for "Montenegro" finds
only the places, not a rule.

Measured on the maintainer's plan of 2026-10-13 (`C:\Users\Christophe\media-hygiene\reports\
20261013-191349-classify\plan.json`, 52,056 rows, read-only): a date range catches what the
folder-name rules miss, the photos of the same days in a person's folder: Saint-Cyprien 2018
980 files + 481 person-folder files on the same days; Turin 2018 92 + 358; Blankenberge 2017
40 + 41.

## What

- A button **📌 Remember as a rule** (and a key, in the ⌨ panel's *More keys*) on the event
  shown, a dialog prefilled:
  - name: the last folder typed (`Montenegro`);
  - `match = "date_range"`, `dates` = the event's first and last day (`2019-07-12..2019-07-19`),
    editable;
  - `category` = the folder typed (0387's field, without the year);
  - `keep_folders = true` (0391), said in one line: "your folders stay below it".
- Before writing, a preview computed by the server on the plan's rows: "this rule would take
  N files: the X of this event, and Y of other folders on the same days (Photos Chloé: 230)",
  and the existing rules it overlaps (a `date_range` sharing days: the first listed wins).
- Saved into `config.toml` with tomlkit (comments kept, atomic, as `places` does:
  `places/toml_edit.py`, its shared part moved to `classify/rules_file.py`), **above**
  *Existing folders* (the rule list's order decides); read back from the disk and shown
  ("Rule *Montenegro* saved in config.toml at 14:32").
- The event's choice is saved too (the folder typed): *Sort this event now* (0390) works at
  once; the rule serves the next `classify` runs.
- The event card says which rule decided its files ("Decided by the rule *Montenegro*,
  2019-07-12..07-19"), from `PlanRow.rule`.
- `/config` is mounted writable by `mh` for every command (`mh.ps1.j2`: the tool volumes have
  no `:ro`), checked 2026-10-25: no mount change needed.

## Tests

The dialog's prefill from an event; the preview counts against `decide` on the plan; the rule
written above *Existing folders*, comments of `config.toml` kept, read back; a second rule of
the same name refused (`unique_names`); both languages; say that `docs_screenshots` should
run.
