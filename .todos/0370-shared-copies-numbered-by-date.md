# 0370 — `share`: copies numbered by date, so the recipient sees them in order

- **Priority**: Low
- **Batch**: share
- **Depends**: —
- **Files**: `src/media_hygiene/services/share_album.py`, `src/media_hygiene/share/prepare.py`, `tests/integration/test_share_album.py`, `documentation/en/commands/share.md`, `documentation/fr/commands/share.md`

## Context

Review of the feedback of 2026-10-22 (0296), maintainer 2026-10-25. The copies keep the
original's name (`IMG_1234.jpg`, `Delivery.add`) in the album's order: photos of two cameras
mix, and the recipient's viewer sorts by name.

## What to do

1. Order the photos by the moment they were taken (the index's `taken_at`, else the file's
   date), ties by name; name each copy `NNN_YYYY-MM-DD.jpg` (width from the count, at least 3).
2. Folder and zip the same names; *what is said at the end* unchanged (read back from disk).
3. Tests: two cameras mixed → in date order; no date → after, by name; 1,000+ photos → 4 digits.
   Docs en + fr.

## Acceptance

- Sorted by name on the recipient's PC or phone, the photos follow the day.

## Gain

Photos out of order at the recipient: any album of two devices → none (by construction).
