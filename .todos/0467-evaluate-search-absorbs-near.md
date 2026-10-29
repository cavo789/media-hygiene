# 0467 — Evaluate: could search replace `near`?

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_review.py`
- **Needs maintainer**: the decision, after this evaluation

## Why

The maintainer, 2026-10-29: search is the central page; every other page it could absorb is one
less to learn. Evaluate before implementing.

## What

Candidate: near-duplicates review (clean --tier near) as a search filter. List what `near` does that search does not (features, keys, data written), the
cost to add each to search, and what users lose. Recommend keep / absorb; no code change here.
