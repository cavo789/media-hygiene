# 0170 — `sort`: 42 s of 112 s spent outside the moves

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

## Status — PARTIAL (2026-10-15)

### Done
- Measured in the devcontainer (8,000 synthetic 4 KB JPEGs, 200 folders, `sort --yes` run in
  process with every `os.stat`/`os.lstat`/`DirEntry.stat` counted per phase): outside the moves,
  `sort` made **64,243 stat calls** — the two censuses 48,203 (3 per file each: `is_symlink`,
  `is_file`, `stat`), `verify_moves` 16,000 (2 per file), prepare and the workbook 9. Local disk:
  1.2 s in all. *Estimated* for Windows: 42 s / 64,200 ≈ 0.65 ms per call on Docker Desktop's
  share, which matches what one call crossing the VM costs — so the stats explain the 42 s.
- `census` reads the folder listing with `os.scandir` (file / folder / link told apart without a
  call) and stats each file once: 48,203 → 16,000 calls (measured, same tree). `verify_moves`
  uses one `stat` for "there, a regular file, its size": 16,000 → 8,000. Outside the moves:
  64,243 → 24,051 calls, **−63 %** (measured). Same proof: both censuses stay, every move is
  still checked; `test_the_census_counts_what_it_counted_before` keeps the old `os.walk` census
  as the reference (links to files and folders, a broken link, a pipe, junk in any case,
  nested and missing roots).
- `--verbosity verbose`: `sort` ends on `Time per step: plan checks · counts · moves · cache
  update · move checks · manifest` (the audit's line, `Stage` and `Stopwatch` extended), which
  `mh-measure.ps1` step 7b/7d already keeps (`$wanted` matches `Time per step`).
- `Duration` keeps meaning the moves (the outcome table's figure); the stage line now shows the
  rest. Recommendation: no change — a whole-run duration would mix in the confirmation wait.
- `services/sort_models.py` (new): `Prepared` and `SortResult` moved out of `services/sort.py`
  (193 lines, cap 200).

### Not done
- The Windows timing: `mh-measure.ps1 -Only 7 -Count 4000` with an image built from this
  change, to confirm the estimate (wall time of 7b before ≈ 112 s for 8,000 files; expected
  ≈ 112 − 40,200 × 0.65 ms ≈ 86 s, *estimated*).
  **Reason:** only the maintainer's PC has Docker Desktop on Windows.
- Not in this TODO's scope, seen while measuring: the moves themselves cost 4 stats per file
  (32,003 for 8,000) and 54 s here on a local disk (≈ 6.7 ms per file, probably the journal's
  per-entry sync — to measure). Worth its own TODO once the Windows stage line says how much
  of the 70 s `Duration` it is.
  **Reason:** the TODO is about the time outside the moves.
