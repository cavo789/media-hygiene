# 0400 — layout: the month of the event (its start), and month 00 when only the year is known

- **Priority**: High
- **Batch**: sort
- **Depends**: —
- **Files**: `src/media_hygiene/classify/engine.py`, `src/media_hygiene/classify/years.py`, `src/media_hygiene/classify/layout.py`, `src/media_hygiene/classify/dates.py`, `src/media_hygiene/classify/plan_rows.py`, `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`

## Why

Decided with the maintainer on 2026-10-25: every file is sorted into
`YYYY/YYYY-MM/<event name>` (0401), and **the month is the month the event starts**. An
event from 28 August to 5 September goes whole to `2009/2009-08/…`. In Explorer, people
look by year first, then month, then event. A file whose month is unknown (a folder that
gives only the year, a scan) gets **month `00`**: `1985/1985-00`. A digit, not a word,
because a word ties the folder to one language. `00` sorts before January and reads as
"the year in general" (the maintainer chose it over `99`).

Read in the code (2026-10-25), not measured:

- `{year}` already follows the event: with `[classify] event_year = "start"` (the
  default), `year_folders` gives an event the year of its start, and a meaningful folder
  the year of its oldest file (`classify/years.py`).
- `{month}` does not: `engine._propose` sets `month=when.month`, the file's own date
  (`classify/engine.py:166`). With `{year}/{month}/…`, the September photos of that
  event would go to `2009/09/…`: one event cut in two.
- A folder that gives only a year is dated **1 July** (`folder_dating`, `month or 7`,
  `classify/dates.py:198`): with a month in the layout, those files would land in
  `YYYY-07`, a month that means nothing.

## What to do

1. `{month}` (and `{month_name}`, `{quarter}`) take the month of the moment that gives
   `{year}`: the event's start, or the oldest file of a meaningful folder, when
   `event_year = "start"`. `per_file` keeps the file's own month. Year and month always
   come from the same date: an event from 31 December 2009 to 1 January 2010 goes whole to
   `2009/2009-12`.
2. Keep "month unknown" in the dating (the July default stays only for ordering or
   the events): `{month}` renders `00` then. Check what EXIF `0000:00:00` / a month `00`
   already gives (`dates.py:47`).
3. Add `{year_month}` (`2009-11`, `1985-00`) so that 0401's layout reads
   `{year}/{year_month}/{category}`, or render `{year}-{month}`: choose whichever keeps
   `layout` checks simple (`layout.py`, `PLACEHOLDERS`).
4. Docs (both languages): the placeholders, "the month of the event's start", month `00`.

## Tests

- An event spanning two months: every file has the start month.
- A New Year's Eve event: year and month of the start for every file.
- A meaningful folder over two months: the oldest file's month.
- A folder giving only the year: `00`; `per_file` unchanged.
