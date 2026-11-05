# 0468 — Evaluate: could search replace `slideshow`?

- **Priority**: Low
- **Batch**: search
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_slideshow.py`

## Why

The maintainer, 2026-10-29: search is the central page; every other page it could absorb is one
less to learn. Evaluate before implementing.

## What

Candidate: slideshow: already reachable from search's 📺 On the TV. List what `slideshow` does that search does not (features, keys, data written), the
cost to add each to search, and what users lose. Recommend keep / absorb; no code change here.

## Decided (2026-11-05, maintainer, start of /todo:iterate)

Run the evaluation unattended and write it into this TODO, with its recommendation (keep / absorb).
The keep/absorb decision stays the maintainer's, asked on the pull request; no code change, no page
removed.

## Evaluation (2026-11-05, unattended; read from `commands/slideshow.md` and `slideshow/`, 3 109 lines counted by `wc -l`, costs estimated)

| What `slideshow` does that `search` does not | Cost to add to search (estimated) |
|---|---|
| The screen page on the TV, black, a photo fitted, and it survives a reload | Already reused: 📺 *On the TV* sends to it; it cannot be a search page |
| The remote on the phone (◀ ▶, pause, time per photo, *Do not show*, a tap on a thumbnail) | Very high: a phone page and its pairing |
| Event names, place line, storyteller's notes, order | High: they belong to the show |
| Start from `--folder`, `--search`, `--album` | None: already picking in search then 📺, except with no page open |
| Data written: none in the photos; its own state for the show | — |

**Users lose if absorbed**: the TV and the remote. So only the *start* can be absorbed, and it
already is; the engine stays whatever the decision.

**Recommendation: keep the engine and its pages.** To decide with the "CLI only if useful in
console" rule: should the verb stay in `mh --help`, or the home page's **Share** alone lead to it?
Decision: the maintainer's.
