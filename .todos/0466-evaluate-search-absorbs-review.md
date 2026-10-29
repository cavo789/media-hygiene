# 0466 — Evaluate: could search replace `review`?

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_review.py`
- **Needs maintainer**: the decision, after this evaluation

## Why

The maintainer, 2026-10-29: search is the central page; every other page it could absorb is one
less to learn. Evaluate before implementing.

## What

Candidate: bursts review: a 'bursts' filter and pick the best shot. List what `review` does that search does not (features, keys, data written), the
cost to add each to search, and what users lose. Recommend keep / absorb; no code change here.
