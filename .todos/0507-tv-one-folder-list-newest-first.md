# 0507 — TV from the phone: one folder list, newest first

- **Priority**: Medium
- **Batch**: phone
- **Depends**: none
- **Files**: `src/media_hygiene/services/slideshow_choices.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/home_texts_family.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_tv_choices.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Reported (maintainer, 2026-10-30)

On the phone's home page, two drop-down lists start a slideshow on the TV (0455):
**"A folder"** (`tvFolder`) and **"A month"** (`tvMonth`). "A month" is newest first — exactly
what is wanted ("here are our latest holiday photos"). "A folder" is not: it is sorted
alphabetically. And the two lists overlap: they show the same folders, "A folder" being the
more complete one. Keep only one list?

## Analysis (code read 2026-10-30)

`Chooser.answer` (`services/slideshow_choices.py`):

- folders: `sorted(_folders(...), key=str.casefold)` — every parent folder of an indexed file
  under `/data`, by its Windows path, alphabetical (`C:\Photos\2019\…` before `C:\Photos\2024\…`).
- months: `SELECT DISTINCT substr(day(media_date), 1, 7) … ORDER BY month DESC` — the dates
  the audit read (EXIF), not the folders. They only *look* like the same list because the
  maintainer's folders are named by date (`2024-08 Vacances`…).

So "A month" is a different filter (a month across every folder) but, for a collection sorted
by date folders, it is redundant and the folder list is what the user means.

## To do

1. **One list**, "A folder" (label could become "Photos of…" / "Des photos de…" — decide at
   implementation), ordered by the **most recent `media_date` of its files**, descending
   (falling back to the newest mtime when no file has a date; folders without any date last,
   then by name). One SQL query (`GROUP BY` parent folder, `MAX(media_date)`) instead of
   reading every path then sorting in Python.
2. **Remove "A month"** from the phone page: `tvMonth` text, the `months` key of `/choices`,
   the month branch of `tvChoose`. Keep the `first`/`last` path of `/choose` only if another
   caller uses it (grep; otherwise remove it and its test, and the now unused msgid
   "No photo or video was taken in this period." if nothing else uses it).
3. Readable on a phone: the option shows the folder's **last part(s)** (e.g. `2024-08 Vacances`),
   not the whole `C:\Users\…\Photos\2024\2024-08 Vacances`; the value stays the full listed
   name (matched as text, as today). Two folders with the same last part: add the parent.
4. Tests in `tests/unit/test_tv_choices.py`: order by newest date (a folder named `zzz`
   with 2026 photos before `aaa` with 2019 ones), undated folder last, display label vs value,
   no `months` key.
5. Docs (en + fr): the page describing the TV from the phone, if it names "A month"
   (grep `documentation/*/`); `i18n_update` + French translation; say that
   `docs_screenshots` should run if a capture shows the lists.

## Gain (estimated)

One list instead of two on a small screen; the latest holidays at the top of it (today: at
the bottom of an alphabetical list, a scroll through every folder — hundreds on the
maintainer's collection, estimated from the per-month folder layout).

## Open question for the maintainer

Is "a month across every folder" ever useful (photos of one month spread over several
folders, e.g. phone + camera)? If yes, keep it as a second choice *below* the folder list,
not removed. Default of this TODO: removed.
