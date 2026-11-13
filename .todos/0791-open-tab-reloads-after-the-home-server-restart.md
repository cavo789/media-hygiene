# 0791 — The open tab reloads by itself after the home server restarts

- **Priority**: Low
- **Batch**: home
- **Depends**: —
- **Needs maintainer**: a Windows run: add a step to `tests/measure/mh-measure.ps1` (PowerShell 5.1) and run it on the maintainer's PC
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `tests/measure/mh-measure.ps1`

Split from 0731 (left by 0359, `.todos/PARTIAL/PARTIAL_0359-home-server-follows-usb-sticks-and-the-nas.md`), one TODO per item as decided by the maintainer on 2026-11-13 (`.claude/plans/feedback-2026-11-13-iterate.md`). The source TODO has the full wording; check the code first, the item may already be done.

## Item

The open tab reloads by itself after the restart (0354's `X-Media-Hygiene-Run`): not re-tested in 0359. Note: on WSL a stick plugged in later is not mounted at /mnt/<x> by WSL itself (`mh_drives.sh.j2`), the bash follow-up works on native Linux only. The Windows run of 0359 (`mh-measure.ps1 -Only 37`) belongs here.
