# 0469 — Evaluate: could search replace `places`?

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_places.py`
- **Needs maintainer**: the decision, after this evaluation

## Why

The maintainer, 2026-10-29: search is the central page; every other page it could absorb is one
less to learn. Evaluate before implementing.

## What

Candidate: places map: a place filter in search (map picker). List what `places` does that search does not (features, keys, data written), the
cost to add each to search, and what users lose. Recommend keep / absorb; no code change here.
