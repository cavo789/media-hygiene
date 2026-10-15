# 0168 — `sort`: 42 s of 112 s spent outside the moves

- **Priority**: Medium — `sort` of 8,000 files on Windows: ≈ 42 s of 112 s are not the moves (measured, `measures-20261015-1429`)
- **Batch**: journal
- **Depends**: —
- **Files**: `src/media_hygiene/services/sort.py`, `src/media_hygiene/actions/manifest.py`, `src/media_hygiene/actions/sort_folders.py`, `tests/measure/mh-measure.ps1`

## Context

0163 measured on the maintainer's machine (Docker Desktop, 8,000 files, 4,755 MB): `sort`
shows `Duration 1 min 10 s` (the moves, 4 at once) but `docker run` lasts 111.8 s; one file at
a time, 82 s against 125.1 s. About 42 s every time, while `undo` of the same sort spends ≈ 3 s
outside its `Duration` (28 s against 31.3 s) — so container start-up is not it.

Outside `_act` in `services/sort.py`, for every file: `prepare` (`check_destinations`, the
empty-folder `candidates`), `census` of the roots **twice** (before and after), `verify_moves`
(a stat per moved file), `_follow` (index rows moved), `write_manifest`. *Estimated*: three
passes of 8,000 stats at ≈ 1.5 ms on Docker Desktop's share ≈ 36 s — to be measured, not
assumed (skill `measure-before-ranking`).

## What to do

1. Time each phase (`prepare`, census before, moves, `_follow`, `verify_moves`, census after,
   manifest) in the verbose log, so `mh-measure.ps1` step 7b reports them; measure in the
   devcontainer first (synthetic tree), then ask the maintainer for one run of `-Only 7`.
2. Only then cut what dominates: e.g. one census instead of two (the moves already say what
   left and arrived), `verify_moves` reusing the stat the move made, the index update in one
   transaction. Every proof `sort` gives today (nothing lost, counts before/after) must stay:
   an equivalence test per change.
3. Say whether `Duration` should cover the whole run (users read it as the time `sort` took).

## Acceptance

- The phases are timed in the verbose log; the 42 s are explained by measurement.
- If a phase is cut: `sort` of 8,000 files on Windows, wall time before → after, measured.
