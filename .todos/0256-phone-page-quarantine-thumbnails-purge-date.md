# 0256 — `mh phone --free` page: set-aside tiles show the quarantine copy; the purge date is journaled and shown

- **Priority**: Low
- **Batch**: launcher
- **Depends**: 0248
- **Files**: `src/media_hygiene/review/phone_views.py`, `src/media_hygiene/review/phone_file.py`, `src/media_hygiene/services/phone_holdings.py`, `src/media_hygiene/actions/purge.py`, `src/media_hygiene/actions/remembered.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_phone_review.py`

## Context

Deviations of 0248 (commit 64e5337), accepted by the maintainer in the review of 2026-10-19 with
this follow-up:

- The tiles of case 3 (a photo set aside on purpose: burst, near copy, unwanted) show a generic
  picture, not the photo: the user decides whether to delete it from the phone without seeing it.
- The warning of a purged one says "purged since", without a date: `purge` does not journal when
  it removed a file.

## What to do

1. Case 3 still in the quarantine: the tile shows the quarantine's copy (served like the other
   thumbnails, read-only, its path checked to lie in a quarantine).
2. `purge` records the date it removed each file (in the run's journal or a small record next to
   it, read by `actions/remembered.py`); the warning says "Purged on <date>: it is nowhere else.
   Deleted from the phone, it is lost for good." Older purges without a date keep "purged since".
3. Tests: a tile of a quarantined photo serves its bytes; a purge then the page shows its date;
   an old purge without a date keeps the old line.

## Acceptance

- Integration tests above; the page reads right in French and English.

## Gain

Case 3 decided on the photo itself instead of a generic tile; the warning dated, as 0248's TODO
first asked.
