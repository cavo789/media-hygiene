# 0553 — Search: a Place filter listing my places, and *📍 Place…* on the selection

- **Priority**: Medium
- **Batch**: search
- **Depends**: 0551
- **Files**: `src/media_hygiene/search/statements.py`, `src/media_hygiene/search/query.py`, `src/media_hygiene/search/templates/`, `src/media_hygiene/review/templates/pick_bar.html.j2`, `src/media_hygiene/places/config_photos.py`

## Why

The maintainer, 2026-10-31: the search page has no way to filter by a named place, and no way to
give dozens of photos without GPS a place at once (only three places given by hand so far: one
by one on the map is too slow). Related: 0469 (could search absorb `places`).

## What

- A **Place** filter: a list of the user's places (`classify.places` + hand-placed), each with
  its photo count; a photo is in it by its GPS circle/area or by hand (0551).
- In the pick bar (skill `photo-picking-pages`): *📍 Place…* opens the list, writes the picked
  photos into `places/<name>.toml`, reads the file back and shows the count saved.
- A photo already in a place by GPS is not written again (said in the answer).
- Documentation en + fr; `docs_screenshots` to run afterwards.
