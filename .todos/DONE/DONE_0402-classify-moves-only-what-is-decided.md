# 0402 — classify moves only what is decided: no "To check" / "To sort" folders; received and screenshots

- **Priority**: High
- **Batch**: sort
- **Depends**: 0401
- **Files**: `src/media_hygiene/config/classify_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/classify/bands.py`, `src/media_hygiene/classify/engine.py`, `src/media_hygiene/classify/guesses.py`, `src/media_hygiene/classify/event_folders.py`, `src/media_hygiene/review/sort_progress.py`, `documentation/en/sort/`, `documentation/fr/sort/`

## Why

Decided with the maintainer on 2026-10-25, with 0401's convention:

- The tool writes **no word of its own** into the tree: `To check`, `To sort`,
  `Undated`, `Received and downloaded` change with the locale, and a user may speak
  another language. Only digits (`2009-11`, `1985-00`) and names the user typed.
- **A file moves once, to its real place.** A guess or an unknown file **stays where
  it is** until the user decides in `review-sort` (or `search`, 0403). Gathering the
  undecided files into `YYYY/To sort/…` made a second jumble, and blurred progress (0405):
  everything outside `YYYY/YYYY-MM` is "to do", whoever put it there.
- **Received pictures** (WhatsApp, Messenger) belong in the months with the user's own
  photos: they are family memories, often of an event the user was at. But their date is
  the day they were **received** (WhatsApp strips EXIF; the date comes from
  `IMG-20260512-WA0003.jpg`, to check on real files), so they are **guesses**: joined to
  the nearest event when there is one, to validate.
- **Screenshots** (tickets, receipts, maps) stay **out of the years**, in a folder whose
  name the user writes in a `kind` rule (a name the user typed has no language problem),
  or where they are.

## What to do

1. Defaults: `unsure_layout`, `manual_layout`, `undated_layout`, `received_layout` empty
   (an empty layout already means "stay where it is", `bands.layout_of`). A user who wants
   the old folders can still set them in `config.toml`.
2. A guess (`Band.UNSURE`) still carries its proposed folder in the plan and the
   workbook: `review-sort` shows it, and validating it moves the file there
   (`sort-decisions.json`, as today). Check that `sort` of a validated guess uses the
   `layout`, not the empty `unsure_layout`.
3. A file already in `YYYY/YYYY-MM` (directly), whose date gives that month: stays,
   `in_place`, never proposed to an event again (the user said "nothing special"). Only
   an explicit choice in `review-sort` or `search` moves it.
4. Received pictures dated by their name: a guess (score below `sure`), joined to the
   event whose time is nearest within `merge_gap_hours`, else their month.
5. Screenshots, documents: a `kind` rule may carry its own `layout` without `{year}` (e.g.
   `layout = "{category}/{year}"`); without one, they stay. Say it in the default
   `config.toml` (example rule commented, both languages).
6. Docs: the table "decided → its folder; guess, unknown, undated → stays until you
   decide", in `sort/` (both languages). `docs_screenshots` must then run.

## Before implementing

- Run `clean --tier near` on the received pictures first, the doc should say: many are
  smaller copies of photos the user holds as originals (estimated, not measured).

## Tests

- A guess, an unknown file, an undated file: `folder is None` / stays; validated, it moves
  to the `layout` folder.
- A file in `2009/2009-11` dated November 2009: in place.
- A received picture next to an event: a guess in that event's folder.
- A `kind` rule with its own layout: no `{year}` needed.
