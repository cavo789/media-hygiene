# 0393 — "Your rules": what each rule decided, dead rules removed, a folder-name rule turned into dates

- **Priority**: Medium
- **Batch**: review-sort
- **Depends**: 0392
- **Files**: `src/media_hygiene/review/sort_rules_view.py`, `src/media_hygiene/review/templates/sort_rules.html.j2`, `src/media_hygiene/review/sort_app.py`, `src/media_hygiene/classify/rules_file.py`, `src/media_hygiene/console/classify_rules_view.py`, `src/media_hygiene/classify/plan_file.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`, `documentation/en/commands/review-sort.md`, `documentation/fr/commands/review-sort.md`

## Why

Maintainer, 2026-10-25: "config.toml must be alive: rules that match nothing any more must be
removed", and the old folder-name rules (`match = "path"`) are converted one by one ("it is
quickly done"). Today `classify` only prints *Rules that decided nothing: …*
(`console/classify_rules_view.py`) and the workbook's summary says it; nothing offers to
remove them, nothing tells what a rule did.

Measured on the maintainer's `config.toml` (63 rules: 55 `path`) and plan of 2026-10-13
(read-only, `C:\Users\Christophe\media-hygiene`):

- 6 rules decided nothing: Sun Park 2017, JDay Paris 2016, Neder-Over-Heembeek 2009, Manon on
  Ice 2008, Le Lucana 2008, Fête à Hannut 2006.
- A `path` rule serves once: it reads the old folder name (`vacances saint-cyprien`); once
  `sort` moved the files to `Vacances et sorties/Saint-Cyprien 2018` it matches nothing (the
  existing folder keeps them). Estimated: most of the 55 become dead after the first sort.
- 15 of the 51 `path` rules that decided files took files spread over more than 14 days
  ("Alsace 2017": 2011-01-01..2017-11-01, 664 files; "Communion de Chloé 2017": 2011..2017):
  their pattern catches badly dated photos or other folders. A conversion to dates must
  propose the days of the event holding most of the rule's files, never the extreme dates.

## What

- A **Your rules** view, opened from the review-sort page (a link in the left column; the
  same frame, `page_frame.html.j2`): every `[[classify.rules]]` in the file's order, with what
  it decided at the run the page shows (`PlanRow.rule`: files, first and last day of the
  event holding most of them), the 🌱 built-in ones (`existing_folder`, `event_neighbour`,
  `same_moment`) apart.
- A rule that decided nothing: flagged, **Remove** (one rule, or *Remove the N rules that
  decided nothing* after a list and a question). Written with tomlkit (comments kept,
  atomic), read back and shown. Said at the end of `classify` too, with the way to the view,
  instead of the bare list of names.
- A `path` rule: **Turn into dates**, one by one (the maintainer's choice): the dialog of 0392
  prefilled with its name, its category, the days of the event holding most of its files,
  `keep_folders = true`; the preview says what changes ("+481 photos of Photos Chloé on the
  same days; 12 photos of other days no longer taken"); saved, the `path` rule is replaced
  in place (same position in the list).
- The plan the page runs on is the last `classify`: say so ("as decided by the classify run of
  13/10; run classify again to see the rules you changed at work").

## Tests

The counts per rule against the plan; the 6-rule case (a rule absent from every row) offered
for removal and removed with the comments kept; a `path` rule spread over two events
proposes the larger event's days; the conversion keeps the rule's place in the list; both
languages; say that `docs_screenshots` should run.
