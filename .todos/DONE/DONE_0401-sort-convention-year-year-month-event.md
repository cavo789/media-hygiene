# 0401 — One sort convention: `YYYY/YYYY-MM/<event>`, the rule dialogs ask a name only

- **Priority**: High
- **Batch**: sort
- **Depends**: 0400
- **Files**: `src/media_hygiene/config/classify_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/classify/folders.py`, `src/media_hygiene/review/templates/rule_dialog.html.j2`, `src/media_hygiene/review/templates/sort_review_rule.js.j2`, `src/media_hygiene/search/templates/search_rule.js.j2`, `src/media_hygiene/search/rule_desk.py`, `src/media_hygiene/classify/rules_edit.py`, `documentation/en/sort/`, `documentation/fr/sort/`

## Why

Decided with the maintainer on 2026-10-25, before any big `sort` (the maintainer has
only sorted a few events from the pages so far: 7 runs, about 1,150 files, counted in
their journal):

- The structure must read in Explorer **without media-hygiene** ("the tool may not exist
  in a few years"). People look by year, then month, then event.
- **Every file, every folder**: `2009/2009-11/Anniversaire de Tom`. `2009-11`, not
  `11`: a folder `11` copied alone, or seen in Explorer's search results, does not say
  which year.
- **A file directly in `YYYY/YYYY-MM`** means "looked at, nothing special that month".
- **A stage of a trip is kept** when the user named one: `2019/2019-07/Montenegro/Budva`
  (one level below the event, `keep_folders`).
- The date rules are a trap when they go silently: that day, a `date_range` rule took
  13 photos out of the user's own `Saint Nicolas 2009` folder (another event the same
  evening), and an older `path` rule with a category `Fêtes/Anniversaires/…` kept 30
  others from it. A category with several levels does not fit the convention.

## What to do

1. Default `layout = "{year}/{year_month}/{category}"` (0400's placeholder), in
   `classify_settings.py` and `config.toml.j2`, both languages; `keep_folders` keeps one
   level below the event.
2. `folders.py`: a folder named `YYYY-MM` (and `YYYY`) is a date only, never a meaning,
   so that `2009/2009-11/Anniversaire de Tom` means `Anniversaire de Tom`.
3. The rule dialogs (`review-sort`'s *Remember as a rule*, `search`'s *Make it a rule*,
   *Update a rule…*) ask for a **name**, not a folder path: the field refuses `/` and
   `\`, and the line under it shows the folder that will be made, as `sort` will make it
   (`→ 2009\2009-11\Anniversaire de Tom`).
4. Rules of the user's `config.toml` whose category holds a `/` (written before): say so
   once in `classify`'s summary (the rule's name and its category), with the one-liner to
   change it. Never rewrite them silently.
5. Docs (both languages, `sort/` and the `classify`/`sort` command pages): the convention
   first, with the Explorer view; `docs_screenshots` must then run (do not run it here).

## Out of scope

- What is not decided does not move: 0402.
- The month of an event and month `00`: 0400.

## Tests

- The default layout gives `2009/2009-11/<category>`; a stage stays one level below.
- `2009-11` and `2009` are generic folder names; `2009/2009-11/X` means `X`.
- The rule dialog refuses a name with a separator and shows the final folder.

## Decided (maintainer, 2026-10-25): the user's own `config.toml`

The maintainer's `config.toml` sets `layout = "{year}/{category}"` (and band layouts)
explicitly, so new defaults do not reach it. **Rewrite with consent**: a command
(`mh config`, a sub-command or option to choose) proposes to move the layouts
(`layout`, `unsure_layout`, `manual_layout`, `undated_layout`, `received_layout`) to the
convention, shows old → new, asks, rewrites `config.toml` with tomlkit (comments kept,
atomic), then reads it back from the disk and shows it. `classify` says once, when a layout
differs from the convention, the one-liner of that command. Never rewritten silently.
