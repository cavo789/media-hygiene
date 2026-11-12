# 0731 — What 0359 left: The home server follows a USB stick plugged in later and the NAS switched on later

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `.todos/PARTIAL/PARTIAL_0359-home-server-follows-usb-sticks-and-the-nas.md`, `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_nas.ps1.j2`, `src/media_hygiene/cli/templates/mh_guards.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `tests/unit/test_launcher_home.py`

Split from section 0359 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/PARTIAL/PARTIAL_0359-home-server-follows-usb-sticks-and-the-nas.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The NAS checked every minute (asynchronous port 445), item 2's NAS half, and item 4 (a NAS
- Item 3: *Remove the USB stick* button and `mh eject E:`. **Reason:** scope.
- Item 5: files of a missing folder opened from search/browse say *not plugged in*. **Reason:** scope.
- *Also*: `mh search` in another window opening the tab on the running home server. **Reason:** scope.
- That the open tab reloads by itself after the restart (0354's `X-Media-Hygiene-Run`) is not

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
