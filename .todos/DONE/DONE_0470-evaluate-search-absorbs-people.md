# 0470 — Evaluate: could search replace `people`?

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_people.py`

## Why

The maintainer, 2026-10-29: search is the central page; every other page it could absorb is one
less to learn. Evaluate before implementing.

## What

Candidate: people page: a person filter in search. List what `people` does that search does not (features, keys, data written), the
cost to add each to search, and what users lose. Recommend keep / absorb; no code change here.

## Decided (2026-11-05, maintainer, start of /todo:iterate)

Run the evaluation unattended and write it into this TODO, with its recommendation (keep / absorb).
The keep/absorb decision stays the maintainer's, asked on the pull request; no code change, no page
removed.

## Evaluation (2026-11-05, unattended; read from `commands/people.md`, `people/` and `search/people_*`, 3 588 lines of `people/` counted by `wc -l`, costs estimated)

`library` already has: `person:` words, a name's chip on each tile with ✕ (reject), *Put back*,
*Why this name?* and *Yes, it is them*, all through the same `people.changes` functions.

| What `people` does that `library` does not | Cost to add to library (estimated) |
|---|---|
| Find the faces (detection, then grouping), with `--path`, `--sample`, `--forget` | None to the page: console work; the verb stays anyway, it computes |
| The groups of **faces**, not photos: crops, largest first, fold, *only this person* | High: the unit is a face, the tile grid's is a file; `pick_*` gestures do not fit |
| Name a group; suggestions; the same person twice merged (*alike*) | High: its own flow, and `/config/people/<name>.toml` written with `verified` / `rejected` |
| Confirm or reject face by face, in bulk | Medium: one face exists in search (*Why*), not the list |
| *Next to do* (g), what is left to name, the guide | Medium: a to-do list with no meaning in a search |
| Ignore a group, hide a person | Low to medium |
| Remove every photo of someone (`aside`), `/person` | Low: in search by `person:` then Ctrl+A, *Set aside*, *Pick all N found* |
| Keys: ↑ ↓ j k o n y g x i / | Clash with the grid's (arrows, I, Space) |

**Users lose if absorbed**: naming faces at speed by keyboard, the whole reason of the page, or
`library` gets a second, different model. The person *filter* the TODO names is already there
(`person:`); only a pick list of names in the left column is missing (cost: low, as the Place one).

**Recommendation: keep `people`**, and add that list of names to `library`'s left column if wanted
(to file on the maintainer's word). Its verb stays in `--help`: it computes. Decision: the
maintainer's.
