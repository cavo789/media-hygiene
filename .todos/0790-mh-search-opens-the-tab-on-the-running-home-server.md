# 0790 — mh search in another window opens the running home server's tab

- **Priority**: Low
- **Batch**: home
- **Depends**: —
- **Needs maintainer**: a Windows run: add a step to `tests/measure/mh-measure.ps1` (PowerShell 5.1) and run it on the maintainer's PC
- **Files**: `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `tests/measure/mh-measure.ps1`

Split from 0731 (left by 0359, `.todos/PARTIAL/PARTIAL_0359-home-server-follows-usb-sticks-and-the-nas.md`), one TODO per item as decided by the maintainer on 2026-11-13 (`.claude/plans/feedback-2026-11-13-iterate.md`). The source TODO has the full wording; check the code first, the item may already be done.

## Item

*Also*: `mh search` typed in another window opens the tab on the home server already running instead of a second server.
