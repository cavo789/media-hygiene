# 0815 — People plan: scanned and turn-guessed photos in one query

- **Priority**: Low
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/services/people.py`, `src/media_hygiene/index/face_rows.py`, `src/media_hygiene/index/turn_rows.py`

Found by 0794. Measured (pages bench, 100,000 synthetic files, py-spy at 50 Hz): `PeopleStep.plan` takes 1.8 s of the people page's cold open (14.9 s profiled): `people_photos` 1.0 s (index listing, `facts_of`, `Path` objects), then one SQL lookup per photo in `FaceStore.scanned` and `TurnStore.guessed` (0.7 s together, ~90k photos × 2 queries).

Do: read the scanned and the guessed (path, size, mtime) of the model in one query each into sets, and test membership; keep `scanned`/`guessed` for single photos. Test: same `PeopleWork` as today on a library with unscanned, changed (other mtime) and turn-missing photos.

Gain, estimated: −0.6 s of the cold open (two set builds from ~90k rows ≈ 0.1 s), also every `mh people` run. Small next to 0814.
