# 0801 — Import counts set-aside copies

- **Priority**: Low
- **Batch**: import
- **Depends**: —
- **Files**: TBD

Follows PARTIAL 0785 (`.todos/PARTIAL/PARTIAL_0785-home-page-import-period-buttons.md`, commit 22090cd3); decided by the maintainer in the review of 2026-11-13 (`.claude/plans/feedback-2026-11-13-iterate.md`).

The import's end line also counts the copies set aside, read from a small file the import writes in /reports (never /config). The mh menu period stays as is (decided).

## Status — DONE (2026-11-27)

`phone-end --copies` writes `import-copies-aside.json` in /reports (`services/import_aside_count.py`); the end line reads it once and says *N copies set aside*. Test: `test_import_period_bursts.py`. The mh menu period is untouched (decided).
