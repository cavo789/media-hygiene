# 0214 — `classify`: a camera's clock off by an hour or a day, set right by a rule; dates in the future doubted

- **Priority**: Low
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/config/classify_settings.py`, `src/media_hygiene/config/clock_settings.py` (new), `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/classify/clocks.py` (new), `src/media_hygiene/classify/dating.py`, `src/media_hygiene/classify/models.py`, `src/media_hygiene/classify/workbook/rows.py`, `src/media_hygiene/tags/dates.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_classify_clocks.py` (new), `documentation/en/sort/06-write-down-what-you-know.md`, `documentation/fr/sort/06-write-down-what-you-know.md`

## Context

Chosen by the maintainer on 2026-10-17 (proposal F8). The photos of one event taken with two
devices — a phone and a camera — interleave wrongly when one clock is off: an hour (summer time,
a trip abroad), a day, a year. `classify` cuts events by time gaps, so a wrong clock splits an
event or merges two.

`classify` already sets aside a camera whose EXIF year disagrees with its folders most of the time
(`classify/dates.py`, `clock_not_set`), at the level of the year only. digiKam (Time Adjust) and
Lightroom (Edit Capture Time) let the user shift capture times inside the photos; here the shift is
written once in `config.toml`, never into a photo (the user's way: "write down what you know",
sorting step 6).

## What to do

- `[[classify.clocks]]`, one table per rule:
  - `camera`: a regular expression on the make and model, as the `camera` rule;
  - `dates = "2010-07-01..2010-07-15"`: the camera's own (wrong) dates the rule covers;
  - `shift = "+1h"`: `+` or `-`, then days `d`, hours `h`, minutes `m`, combined (`-1d2h`).
  Validated with the other settings: a bad shift or range is refused, naming the rule; two rules of
  one camera whose ranges overlap are refused, naming both. `classify_settings.py` is at 196/200:
  the new model goes to `config/clock_settings.py`.
- Applied to the EXIF dates of the matching files in the date chain (`classify/dating.py`, a new
  `classify/clocks.py`) and in `tags` (`tags/dates.py`: year, month, season words); the workbook
  says it on the file's row ("+1h: rule <camera>"). `classify/models.py` is at 194/200: if `Dating`
  needs a field for the shift, move a model out to a new module first.
- A date in the future (after the day of the run) is doubted: the file goes to "to check" with that
  reason, as a year its folder contradicts does.

## Explicit non-goals

- Writing the shift into the photos or their `.xmp`.
- `search`'s year filter (it reads the index's `media_date`, 0197).
- Guessing shifts by itself (comparing two cameras' shots of one moment): a later idea.

## Acceptance

- Unit (`test_classify_clocks.py`): parsing (shifts, ranges, refusals), applied only inside the
  range and to the matching camera, overlaps refused, `tags` words follow, a future date doubted;
  `config.toml.j2` holds a commented example.
- Docs both languages: sorting step 6, a section with an example (a trip abroad, the camera an hour
  behind).

## Gain (estimated)

An event photographed with a phone and a camera an hour apart stays one event, in the right order,
without editing a single photo.
