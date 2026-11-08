# 0656 — Check on real photos what the date in `IMG-YYYYMMDD-WA` names

- **Priority**: Low
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/classify/received.py`

## Problem

Follows 0402 (feedback of the sort convention run, 2026-10-25). Received pictures are joined to
the event nearest the **day of their name**, assuming `IMG-YYYYMMDD-WA` holds the day they were
received. Not checked on real files. Decided in the review of 2026-11-08: check it read-only on
the maintainer's collection.

## Fix

Read-only (the `C:\Photos` mount, `:ro`; nothing written there): list the `*-WA*` files that also
carry an EXIF date, compare that date with the one in the name (same day, days before, after),
and give the distribution (*measured*). If the name's date is often later than the taken day,
adjust `classify/received.py` (wider window, or before only) and its tests.

## Acceptance

- [ ] The distribution measured and written here (count, median gap, how many are the same day)
- [ ] `received.py` changed only if the measure says so, with a test
