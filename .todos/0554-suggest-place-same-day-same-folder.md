# 0554 — Suggest the same place for photos of the same day and folder

- **Priority**: Low
- **Batch**: search
- **Depends**: 0553
- **Files**: `src/media_hygiene/search/`, `src/media_hygiene/places/config_photos.py`

## Why

Once a few photos without GPS are placed, their neighbours (same day, same folder) were very
likely taken at the same place. The user confirms; nothing is placed without a Yes.

## What

- After *📍 Place…*, the answer offers: "23 other photos of the same day and folder: same
  place?", shown as tiles (pick out the exceptions), then saved and read back.
- Only photos without GPS and without a place yet.
