# 0793 — CI: integration tests in two balanced jobs

- **Priority**: Medium
- **Batch**: tests
- **Depends**: —
- **Files**: `.github/workflows/ci.yml`

Follows PARTIAL 0734 (`.todos/PARTIAL/PARTIAL_0734-left-by-0423-ci-tests-job-off-the-critical-path.md`, commit f443504b); decided by the maintainer in the review of 2026-11-13 (`.claude/plans/feedback-2026-11-13-iterate.md`).

Measured on PR #82 (CI job durations): unit 159 s, integration 369 s, e2e 258 s; integration is the critical path. Split `Tests (integration)` in two jobs of about equal duration (by directory, balanced by the measured per-file durations, `--durations`), coverage combined as today. Expected: about 185 s per half (estimated: 369 / 2), the critical path then e2e at 258 s. No check names to keep in sync: main has no branch protection (checked by the maintainer).

## Done (2026-11-13)

`Tests` matrix: `unit`, `integration-1`, `integration-2`; each integration half takes every other file of the sorted `tests/integration/**/test_*.py` list (100 + 100 files, counted); coverage combines the three data files. Interleave instead of a duration packing: CI logs only the 15 slowest tests, not each file's time. Expected ≈ 185 s per half (estimated: 369 s / 2), critical path then e2e (258 s); the PR's CI measures it.
