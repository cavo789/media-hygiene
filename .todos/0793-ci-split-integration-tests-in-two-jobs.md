# 0793 — CI: integration tests in two balanced jobs

- **Priority**: Medium
- **Batch**: tests
- **Depends**: —
- **Files**: `.github/workflows/ci.yml`

Follows PARTIAL 0734 (`.todos/PARTIAL/PARTIAL_0734-left-by-0423-ci-tests-job-off-the-critical-path.md`, commit f443504b); decided by the maintainer in the review of 2026-11-13 (`.claude/plans/feedback-2026-11-13-iterate.md`).

Measured on PR #82 (CI job durations): unit 159 s, integration 369 s, e2e 258 s; integration is the critical path. Split `Tests (integration)` in two jobs of about equal duration (by directory, balanced by the measured per-file durations, `--durations`), coverage combined as today. Expected: about 185 s per half (estimated: 369 / 2), the critical path then e2e at 258 s. No check names to keep in sync: main has no branch protection (checked by the maintainer).
