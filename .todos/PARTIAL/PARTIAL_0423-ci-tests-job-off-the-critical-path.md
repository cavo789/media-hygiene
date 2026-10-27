# 0423 — CI: the Tests job is the critical path, its slowest tests first

- **Priority**: Low — about one minute per CI run, nothing a user sees
- **Batch**: tests
- **Depends**: —
- **Files**: `.github/workflows/ci.yml`, `tests/integration/test_sort.py`, `tests/support/docs/`, `tests/unit/test_launcher_comfort.py`, `tests/integration/test_places_tree.py`, `tests/integration/test_places_folders.py`

## Why

Since fb353e3 every CI job starts at once (`publish` alone waits). A run lasts as long as its
longest job. Measured on run 40485254592 (fb353e3, green), from the job and step timestamps:

| Job | Duration | What takes the time |
|---|---|---|
| Tests | **289 s** | pytest 277 s (`-n auto --dist worksteal`, 4 workers, 3778 tests) |
| Image end-to-end tests | 230 s | image build 64 s, `pytest -m e2e` 130 s |
| Lint, types | 82 s | pre-commit 71 s |
| Image amd64 / arm64 | 42 s / 41 s | |

The Tests job is the critical path. Shortening it by up to about 60 s (−20 % of the run,
*estimated*: 289 → about 230 s) shortens the run; past that, the e2e job becomes the longest one.

pytest has varied between 212 s and 375 s over the last twelve runs (*measured*, same source).
Compare medians over several runs, never single runs.

## The slowest tests (`--durations=15`, same run)

- `tests/integration/test_sort.py::test_the_documentation_library_without_clean_settles_after_one_sort`:
  **25.7 s** `[en]` + **22.6 s** `[fr]`. It builds the whole documentation library twice
  (`build_docs_library`), then classifies, sorts and classifies again.
- `tests/unit/test_launcher_comfort.py::test_bash_opens_the_browser_once_the_page_answers`:
  **10.6 s**, in a *unit* test. Probably a real wait for a page (to check).
- `test_places_tree.py`, `test_places_folders.py`, `test_xmp_folder_gps.py`: 5–9 s each,
  seven tests.
- Collection and starting the workers: about 15 s (08:44:30 → 08:44:45 on run 40475497669).

## What to do

1. Measure first (skill `measure-before-ranking`). With `--durations=0` in a CI run, how much do
   the 15 slowest tests weigh in all? What do the setup phases (fixtures) cost? Is the end still a
   tail? On 6cc9187 the last 7 % took 82 s of 319 s. Was that tail gone with `worksteal`?
2. `test_sort` docs library: build the library once per locale in a module-scoped fixture (a
   copy per test if the test moves files), or a smaller library that still covers the same
   cases. The two parameters probably exercise the same code paths: does `[fr]` cover anything
   `[en]` does not (to check)? Equivalence: the same assertions.
3. `test_launcher_comfort`: find what waits 10 s (a timeout, a polling loop of the launcher),
   then make it configurable in the test or shorter, without testing anything less.
4. If, after 1–3, the Tests job is still longer than the e2e job, split it into two parallel
   jobs: `tests/unit` and `tests/integration`, `coverage combine` in a small job, threshold
   unchanged. That costs one more runner and some YAML: decide it after the measurement.

## Acceptance

- Over at least three green runs, the median of the Tests job is ≤ the median of the e2e job,
  or there is a measured reason why not.
- The commit says before → after (medians, runs cited).

## Not in scope

The Playwright image (about 2 GB, pulled on every run: GitHub's runners are fresh machines).
Since 88cf550 it is pulled in the background while the image builds. On run 40485254592 the pull
started at 10:01:57 and the browser test at 10:04:12 (*measured*), so the pull no longer costs
anything on the run's duration. Caching it (`docker save` into `actions/cache`) would not shorten
the run, and it would use up most of the repository's Actions cache, which the buildx and ffmpeg
caches also need.

## Status — PARTIAL (2026-10-27)

### Done
- `test_bash_opens_the_browser_once_the_page_answers`: the 10 s were the fake `docker`
  waiting for the browser on **every** call, the launcher's `docker ps` included (traced
  with `PS4=$EPOCHREALTIME`: 10.4 s on `docker ps`, before any browser could open). It now
  waits on `docker run` only: 10.31 s → under 1 s (*measured* locally, `--durations`),
  same assertions.
- `test_sort` documentation library, measured locally: 11 s per locale, of which 8 s build
  the library (profile: 6.3 s `write_shot`, of which 2.6 s grain + 1.6 s Gaussian blur of the
  synthetic pictures, 1.4 s ffmpeg videos, 1.1 s HEIC encoding). Kept as is: `[fr]` covers
  what `[en]` does not (the folder names, accents included, matched against event names);
  a per-process cache would not help since the two locales run on different xdist workers.

### Not done
- Medians of the Tests vs e2e jobs over at least three green runs, and the decision to split
  the Tests job (`tests/unit` / `tests/integration`, `coverage combine`).
  **Reason:** needs several CI runs after this commit (`ci`, `gh run view --json jobs`);
  expected gain of this commit about 10 s of one worker, ≈ 3 s of the run (*estimated*:
  10 s / 4 workers).
- Options left for the documentation library if the Tests job stays the critical path: a
  smaller grain/blur in `tests/support/docs/painting.py` for this test only (pictures no longer
  those of the screenshots), or a disk cache of rendered pictures shared by the workers.
