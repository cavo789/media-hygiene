# 0197 — EXIF dates written `dd/mm/yyyy`: `search` misreads their year and order, bursts ignore them

- **Priority**: High — a measured bug: 1.2 % of the dated photos of a real collection are missed by `search`'s year filter and left out of burst detection
- **Batch**: tags
- **Depends**: —
- **Files**: `src/media_hygiene/classify/dates.py`, `src/media_hygiene/search/days.py` (new), `src/media_hygiene/search/statements.py`, `src/media_hygiene/search/fts.py`, `src/media_hygiene/search/hits.py`, `src/media_hygiene/plan/bursts.py`, `tests/unit/test_classify_dates.py`, `tests/unit/test_search_index.py`, `tests/unit/test_similar.py`

## Context

Found on 2026-10-17 while measuring the maintainer's index read-only (the `media-hygiene-cache`
volume mounted `readonly`, SQLite `?mode=ro&immutable=1`, 52,094 media files): of 47,301 dated
files, **567** hold an EXIF date written day first (`04/12/2004 11:05:08`, as some cameras write
it) and **12** hold `0000:00:00 00:00:00` (an unknown date).

The index keeps the date as the file writes it (`index/rows.py`: `media_date` is
`visual.taken_at`, or a video's `recorded_at`). `classify.dates.exif_date` reads the three forms
(`_EXIF_FORMATS`), but two readers slice the text as if it always started with the year:

- `search/statements.py`: `YEARS` is `CAST(substr(files.media_date, 1, 4) AS INTEGER)`, so
  `year 2004` misses `04/12/2004` (read as 4); `NEWEST_FIRST` sorts on
  `replace(substr(…, 1, 10), ':', '-')`, so these photos are misplaced; `search/hits.py` shows
  `04/12/2004` instead of `2004-12-04`; `0000:00:00` reads as year 0 and shows `0000-00-00`.
- `plan/bursts.py`: `_EXIF_MOMENT` accepts `YYYY:MM:DD HH:MM:SS[.sub]` only, so a photo dated day
  first never joins a burst series (the 567 photos above are all left out of burst detection).

## What to do

1. `classify/dates.py`: split the parsing from the 1990 floor. A new `exif_datetime(text)` reads
   the three `_EXIF_FORMATS` (sub-seconds dropped, as today) and returns any valid date (year 0,
   month or day 00: None). `exif_date` keeps its floor on top of it, unchanged for its callers
   (classify, tags, inventory, messaging copies).
2. `search`: a SQLite function `media_day(text) -> str | None` in a new `search/days.py`, registered
   next to `fold` in `SearchIndex.__init__` (`create_function(…, deterministic=True)`):
   - fast path first, without `strptime`: `YYYY:MM:DD…` (EXIF) and `YYYY-MM-DD…` (videos, ISO)
     give `YYYY-MM-DD` when they name a real calendar day;
   - otherwise `exif_datetime` (the day-first form) gives its day;
   - else None: undated, out of every year filter, listed last (as an undated file today).
   `YEARS`, `NEWEST_FIRST` and `HITS` use it, and `hits.py` shows the day as is. No floor in
   `search`: an EXIF year before 1990 stays findable by its year, as today.
3. `plan/bursts.py`: `moment_of` also reads `DD/MM/YYYY HH:MM:SS[.sub]`, sub-seconds kept, so
   those photos form series like the others.

## Explicit non-goals

- No index schema change: `media_date` keeps the date as the file writes it (a fact); readers
  parse it.
- `plan/near.py` compares two copies' `taken_at` as text (`other.taken_at == best.taken_at`): two
  copies whose dates are written in two different forms are rare and not measured; left as is.
- Video dates keep their UTC day in `search`, as today (`classify` brings them to local time;
  aligning `search` is another change).
- `tags/selection.py` orders the `--sample` candidates by the raw text: an ordering only.

## Acceptance

- Unit (`test_classify_dates.py`): `exif_datetime` reads the three forms; `0000:00:00 00:00:00`
  and `2019:00:12 10:00:00` give None; `exif_date` unchanged (floor kept).
- Unit (`test_search_index.py`): an index holding `2004:12:04 11:05:08`, `04/12/2004 11:05:08`,
  `2004-12-04T10:00:00Z` (a video), `0000:00:00 00:00:00` and `1985:06:01 10:00:00`: the years
  2004–2004 find the first three, 1985 finds the last, the zero date matches no year and comes
  last; the first three show `2004-12-04`; the newest-first order is the same whatever the form.
- Unit (`test_similar.py`): three shots dated day first, one second apart, form one series, their
  sub-seconds kept.
- Time: a search without words over 50,000 synthetic rows, before → after, measured and reported
  (the fast path must keep the difference small: say the figure).
- Commit gate on the changed files.

## Gain

Measured on the maintainer's index (2026-10-17): 567 photos (1.2 % of the dated ones) found again
by their year, shown and ordered by their real date; 12 zero dates no longer shown as
`0000-00-00`; the same 567 photos can now join a burst series (how many series: one audit after
the change says it).
