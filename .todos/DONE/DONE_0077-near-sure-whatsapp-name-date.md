# 0077 — Sure near duplicates: the date in a messaging file name counts as the EXIF date

- **Priority**: Medium
- **Batch**: near
- **Depends**: —
- **Files**: `src/media_hygiene/plan/near_levels.py`, `src/media_hygiene/classify/dates.py`, `src/media_hygiene/config/classify_settings.py`, `tests/unit/test_near_levels.py`, `documentation/en/clean/11-near-duplicates.md`, `documentation/fr/clean/11-near-duplicates.md`

## Context

TODO 0068 made a near-duplicate group **sure** when each copy moved is, among other reasons, a
smaller copy in a messaging/e-mail folder (`near_levels.MESSAGING_FOLDERS`) **with the same EXIF
date** as the kept version. WhatsApp strips the EXIF of the pictures it sends, so its copies,
the most common shrunk copies of a family collection, stay "to check" and need
`review --near` or `--tier near-all`.

Their names still carry the day: `IMG-20190712-WA0003.jpg`, `VID-20190712-WA0001.mp4`.
`classify` already reads such dates (`classify/dates.name_date` with
`ClassifySettings.name_dates`, the `-WA\d+` pattern included).

## Steps

- [x] In `near_levels.copy_reason`, when the copy is in a messaging folder and has no EXIF
  date, take the date of its name (`name_date`, same patterns as `classify`) and accept it when it
  is the **same day** as the kept version's EXIF date (the name has no time).
- [x] Keep the other conditions (smaller copy, messaging folder); a copy without EXIF nor a
  dated name stays "to check".
- [x] The 💬 reason line says which proof was used (EXIF date, or date in the name), en and fr.
- [x] Unit tests: WhatsApp copy without EXIF, same day → sure; other day → to check; name
  without a date → to check.
- [x] Docs en/fr: the "Sure groups, and those to check" section of `clean/11-near-duplicates.md`.

## Acceptance

- On the demo tree (or a synthetic fixture), a `WhatsApp Images/IMG-YYYYMMDD-WA0001.jpg` shrunk
  copy without EXIF, same day as the original, is in a sure group and moved by
  `clean --tier near`.

## Status

DONE (2026-10-11, night run, second pass). New `SureReason.MESSAGING_NAME` ("messaging-name"),
the least sure reason: a smaller copy in a messaging folder **without** an EXIF/video date whose
name (the built-in `[classify] name_dates` defaults, `NAME_DATES`) gives the same day as the
kept version (EXIF date, or a video's ISO time brought to the container's local zone). A copy
with an EXIF date of its own still needs the same EXIF date. The folder patterns and the day
check moved to `plan/messaging_copies.py` (`near_levels.py` stays under 200 lines). The 💬 line
says the proof: "(same EXIF date)" or "without EXIF date, its name dated the same day".
Integration: the demo's `WhatsApp/IMG-20210705-WA0001.jpg` is moved by `clean --tier near`
once the undated e-mail copy is gone. Report: `.claude/plans/night-2026-10-10/0077-report.md`.
