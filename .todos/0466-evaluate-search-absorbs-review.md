# 0466 — Evaluate: could search replace `review`?

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_review.py`

## Why

The maintainer, 2026-10-29: search is the central page; every other page it could absorb is one
less to learn. Evaluate before implementing.

## What

Candidate: bursts review: a 'bursts' filter and pick the best shot. List what `review` does that search does not (features, keys, data written), the
cost to add each to search, and what users lose. Recommend keep / absorb; no code change here.

## Decided (2026-11-05, maintainer, start of /todo:iterate)

Run the evaluation unattended and write it into this TODO, with its recommendation (keep / absorb).
The keep/absorb decision stays the maintainer's, asked on the pull request; no code change, no page
removed.
