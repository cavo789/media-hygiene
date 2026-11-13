# 0804 — Heavy page states kept while the index and config.toml are unchanged

- **Priority**: High
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/services/places_here.py`, `src/media_hygiene/services/people_here.py`, `src/media_hygiene/search/folders.py`, `src/media_hygiene/search/found_desk.py`, `src/media_hygiene/search/fts.py`, `src/media_hygiene/search/statements.py`, `src/media_hygiene/services/first_warm.py`, `src/media_hygiene/people/people_memo.py`, `tests/measure/pages-budget.md`, `tests/unit/`

Filed by the speed review of 2026-11-13 (asked by the maintainer: *the web pages must
get faster, never slower as the collection and the sorting work grow*; analysis only, no
code changed). Method: `measure-before-ranking`; figures from `tests/measure/pages-budget.md`
(*measured* 2026-11-11, synthetic index, server work only, warm = median of 5).

## Context

Four page builds read the whole index again at **every** visit or request, although
nothing changed between two visits; their warm time equals their cold time:

| What | Where | 100,000 files, warm | 300,000 files, warm |
|---|---|---:|---:|
| `/places/` page (clusters rebuilt at each GET, `places_here._build`) | `services/places_here.py` | 2,422 ms | 14,760 ms |
| `/people/` page (`PeopleStep.plan` + `result` at each GET, `people_here._built`) | `services/people_here.py` | 3,672 ms | not run (≈ 250 s cold, estimated ×9) |
| `GET /api/folders` (every row read, counted in Python, `folder_counts`) | `search/folders.py` | 2,956 ms | 8,852 ms |
| `GET /api/found-events` (`found_folders` over the index) | `search/found_desk.py` | 1,827 ms | 5,536 ms |

The maintainer's library (52,094 media, 27,159 faces, measured 2026-10-17) sits between
the two first columns: *estimated* 1–2 s per visit of the map or the folder view, paid
on the home server's loop, so the previews of the same page wait behind it.

The index already exposes what makes a result stale: `PRAGMA data_version`
(`statements.DATA_VERSION`, used by `SearchIndex.built` to rebuild the full-text table
only when another connection committed). `people_memo` does the same for `config.toml`
and the files it links (signature: inode, size, mtime, ctime). A third input: the index
**file** itself replaced by another one (`shrink`, a restore from `mh backup`): its
signature joins the key, `data_version` alone being per connection.

## Proposal

- One small shared memo (`services/kept_state.py` or near `people_memo`): a value kept
  with the key it was computed under: `(index data_version, index file signature,
  config.toml + linked files signature, the settings layer the CLI gave)`; read again
  only when the key changes. Used by the four builds above (places clusters + folders,
  people board/roster, folder tree, found events). The people page's *Apply now* desk
  and session must survive a kept state: keep the app, refresh only what the key covers.
- A change made **through** the page (a place saved, a face named, a folder's role) goes
  through `config.toml` and is seen by the signature: no manual invalidation; a test per
  event (an edit in place, an atomic save, a copy keeping the mtime, a `touch`, an
  audit in another process, `undo`/`sort` moving files: the cache-invalidation list of
  `.claude/rules/workflow.md`).
- The RAM is there (the maintainer has 64 GB): keep the states of the pages visited,
  and **build them ahead** on the warm-up thread (`first_warm`, 0677) once the home
  server listens and again at the end of an audit run from the home page, so the first
  click is warm too. The warm-up stays low priority and read-only.
- Memory: say in the PR what each kept state weighs (`tracemalloc`) at 100,000 files
  (places + people + folders + events); the pages-budget bench says 1,123 MB peak for the
  people page at 100,000 (face grouping), so the people state is the one to size.

## Acceptance

- [ ] `tests/measure/pages-budget.md` rerun (`python -m tests.measure.pages.bench`): the four
      rows' warm time at 100,000 files below 100 ms (the 0678 target), the cold time unchanged
      or better (built ahead); before/after in the PR, *measured*
- [ ] One test per invalidation event (list above) for each kept state; a change saved from
      the page itself is visible at the next GET (read back from the disk, as every save)
- [ ] The people page keeps its *Apply now* offer and the files set aside across a kept state
- [ ] Memory of the kept states at 100,000 files written in the PR; if above a few hundred MB,
      say whether a `[cache]` setting should bound it (default: keep all; `few-settings`)
- [ ] The measured figures copied into this TODO's closing status

## Where the user gains

Estimated from the table: a second visit of the map, the people page, the folder view or
*Events found* on a 52,000-file library drops from 1–2 s of server work to under 0.1 s
(−90 % or more); on 300,000 files from 5–15 s to under 0.1 s. The first visit after a
start is paid once, ahead, on the warm-up thread.

## Status — PARTIAL (2026-11-13)

### Done
- `services/kept_state.py`: `KeptState` keyed on the index file (inode, size, mtime,
  ctime, header change counter, `-wal`), every file of `/config` but `.history/`, and
  the settings. Used by the map (`places_here`), the people page (`KeptPage`: app kept,
  its session and *Apply now* go on), the folder tree (`FolderDesk.kept`) and *Events
  found* (`FoundDesk.kept`, keyed on the sidecar days too).
- Built ahead by the warm-up (`first_warm`): `/api/folders`, `/api/found-events`, `/places/`.
- `sidecar_days`: `os.listdir` instead of `Path.iterdir` (287 → 126 ms warm, found events).
- Tests (`tests/unit/test_kept_state.py`): a commit by another connection, a move by
  `sort`/`undo`, an atomic save, a copy keeping the mtime, a `touch`, an in-place
  edit, another process, a `-wal` file; `/config` edit, atomic save, copy, touch, file
  added/removed, `.history` ignored; a renamed photo waits for the audit; the folder
  tree and the people page (built once, again after a name saved).
- Measured (pages bench, 100,000 files, warm): folders 130 → 2.8 ms, found events
  492 → 126 ms, map 2,234 → 0.2 ms; 300,000: folders 7.5 ms, found 374 ms, map 0.1 ms.

### Not done
- *Events found* warm 126 ms at 100,000 (target 100): the sidecar days are listed again
  at each ask (0618). **Reason:** keying them on folder mtimes misses a sidecar edited
  in place; needs a decision.
- People page not measured kept, nor warmed ahead. **Reason:** the bench's synthetic
  library answers 409 (faces not "guessed"); the page's build writes face groups (not
  read-only for the warm-up).
- Warm-up again at the end of an audit run from the home page. **Reason:** not wired; the
  first visit after an audit pays the build.
- `tracemalloc` of each kept state. **Reason:** not measured; estimated from the answers:
  folders 0.9 MB of JSON at 100,000 (2.6 MB at 300,000), found events 0.5 MB, the map's
  app ≈ its 127 KB page plus clusters: tens of MB at most, no `[cache]` setting proposed.
