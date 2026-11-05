# 0467 — Evaluate: could search replace `near`?

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_review.py`

## Why

The maintainer, 2026-10-29: search is the central page; every other page it could absorb is one
less to learn. Evaluate before implementing.

## What

Candidate: near-duplicates review (clean --tier near) as a search filter. List what `near` does that search does not (features, keys, data written), the
cost to add each to search, and what users lose. Recommend keep / absorb; no code change here.

## Decided (2026-11-05, maintainer, start of /todo:iterate)

Run the evaluation unattended and write it into this TODO, with its recommendation (keep / absorb).
The keep/absorb decision stays the maintainer's, asked on the pull request; no code change, no page
removed.

## Evaluation (2026-11-05, unattended; read from `commands/review.md` and `review/near_*`, costs estimated from their size, nothing measured)

| What `review --near` does that `search` does not | Cost to add to search (estimated) |
|---|---|
| Two versions side by side, compared large, group by group | High: the grid shows tiles, not pairs |
| `W` keep the other, `L` leave alone, `U` undecided, `X` none kept, `G` the folder pair as planned | Medium to high: a per-group choice, not a pick |
| Sure groups / to check, the tier's rule explained; contact sheet of the sure groups | High: its own sheet |
| The groups and their proof: from the audit's report (`near`, `near_video`), not in the index | High: search reads the index only |
| `decisions.json` by group, read by `clean --tier near` (kept version, action) | Medium: a flat *set aside* cannot say "keep the other version" |
| Protected folder rule shown (W impossible) | Low |

**Users lose if absorbed**: the comparison itself, which is why the page exists: a near duplicate
is judged against its pair, and a filter would show both copies with no link between them, so an
action could set both aside.

**Recommendation: keep.** Decision: the maintainer's.
