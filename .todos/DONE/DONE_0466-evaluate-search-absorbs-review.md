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

## Evaluation (2026-11-05, unattended; read from `commands/review.md` and `review/`, costs estimated from the size of those modules, nothing measured)

| What `review` does that `search` does not | Cost to add to search (estimated) |
|---|---|
| Series one at a time, `←` `→` `N`, a progress line, the pace, the share of the gain seen | High: a second navigation mode, the keys conflict with the grid's arrows |
| `S` sharpest, `X` all, `V` every obvious series, *Keep every shot*, `Z` undo the last choice | Medium: new bar actions, a choice history |
| The contact sheet of obvious series (about 400 a minute, estimated in the docs) | High: its own layout, `review_sheet` |
| The series and the reason for each shot: the audit report's `bursts`, not in the index | High: search reads the index; a report would become a second source |
| `decisions.json` key `bursts` (keeper and shots by series) | Medium: search writes a flat list of files set aside |
| In common: the pick gestures, the large view, the album field, *Apply now* (shared `pick_*`) | None |

**Users lose if absorbed**: the guided path (series after series) and its speed; a flat grid hides
where a series starts and leaves the judging to the eye of the user over thousands of tiles.

**Recommendation: keep.** Search can link to it, not replace it: about four filters' worth of
page for a worse flow. Decision: the maintainer's.

## Decided (2026-11-05, review of feedback-2026-11-05-iterate)

Keep the page (maintainer). For `slideshow`: the verb is hidden from `mh --help`, still callable.
