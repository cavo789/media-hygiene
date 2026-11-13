# 0787 — Home server: the NAS checked every minute, a NAS asleep shown

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Needs maintainer**: a Windows run: add a step to `tests/measure/mh-measure.ps1` (PowerShell 5.1) and run it on the maintainer's PC
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_nas.ps1.j2`, `tests/measure/mh-measure.ps1`, `tests/unit/test_launcher_home.py`

Split from 0731 (left by 0359, `.todos/PARTIAL/PARTIAL_0359-home-server-follows-usb-sticks-and-the-nas.md`), one TODO per item as decided by the maintainer on 2026-11-13 (`.claude/plans/feedback-2026-11-13-iterate.md`). The source TODO has the full wording; check the code first, the item may already be done.

## Item

The NAS checked every minute (asynchronous port 445): item 2's NAS half, and item 4 (a NAS asleep: a time limit on reads, a *NAS not reachable* tile).
