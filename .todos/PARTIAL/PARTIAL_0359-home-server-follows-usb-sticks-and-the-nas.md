# 0359 — The home server follows a USB stick plugged in later and the NAS switched on later

- **Priority**: Medium
- **Batch**: home
- **Depends**: 0355
- **Files**: `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_nas.ps1.j2`, `src/media_hygiene/cli/templates/mh_guards.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/review/templates/home*.j2`, `tests/unit/test_launcher_home.py`, `tests/measure/mh-measure.ps1`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`
- **Measure (after)**: a step of `tests/measure/mh-measure.ps1` written by the implementation (USB stick plugged in, then removed, during a session; Windows only), run by the maintainer afterwards (decided 2026-10-27)

## Context

Phase 3b of the single server (maintainer, 2026-10-24: "neither the USB stick nor the NAS will be
plugged in / switched on at start"). Docker cannot add a mount to a running container: a stick
plugged in or a NAS switched on **after** the home server started stays invisible to it.

Today (read in the code, 2026-10-24):
- a photo folder of `mh folders add` that is missing makes **every** `mh` command refuse
  (*… cannot be found: plug its disk in*, `mh.ps1.j2`) — the home server must start without it;
- a NAS that does not answer on port 445 within 2 s: one line, the command goes on without it
  (`mh_nas.ps1.j2`, `_nas_up`);
- a stick is shared with Docker Desktop's VM for one command, then released so that Windows can
  eject it (0252).

## What to do

1. The home server starts with the folders present; one line per folder missing (*E:\Photos: not
   plugged in, shown once it is*), never a refusal for the home page.
2. While the server runs, `mh`'s loop (0355) checks the photo folders every few seconds
   (`Test-Path`: milliseconds) and the NAS every minute or so (port 445, asynchronous: never
   blocking the 250 ms loop). A folder appearing or leaving → the server **restarted** with the new
   mounts (about 2–3 s, *estimated* from 35a/35c), one line in the window; the open tab reloads by
   itself (`X-Media-Hygiene-Run`, 0354).
3. **Remove the stick**: Windows cannot eject a drive Docker's VM keeps mounted, and `mh` cannot
   see the Explorer's *Eject*. A *Remove the USB stick* button on the home page (and `mh eject E:`)
   restarts the server without it and releases it; then Windows ejects it. Its docs say so.
4. **A NAS that falls asleep during the session**: reading a file on it may hang (SMB): a time
   limit on those reads, a tile *NAS not reachable* instead of a frozen page; the next check
   restarts the server without it.
5. Files of a missing folder in search and browse: listed by the index, their previews from the
   cache, *not plugged in* when opened (never an error page).
6. Tests (bash fake docker): a folder appearing restarts the server once; the stick's button;
   PowerShell blocks as text. Measure step: stick plugged in during a session, then the button,
   then Windows' *Eject* (asked to the maintainer).

## Acceptance

- Start without the stick and the NAS, plug the stick in: its photos in browse within a few
  seconds, without typing anything; the button, then Windows ejects it.

## Gain

The stick and the NAS usable in a session started without them (today: the session must be
started again, and a missing folder refuses every command).

## Also (inbox, 2026-10-27, from 0356)

`mh search` / `mh browse` typed in another window while this `mh`'s home server runs: open the
tab on that server (found by its container label) instead of starting a second page and asking
to close one (the port guard of 0250).

## Status — PARTIAL (2026-10-29)

### Done
- Items 1–2 for photo folders and backups: the home server (`mh` alone, detached) starts
  without a folder not plugged in (one line *E:\Photos: not plugged in, shown once it is*);
  any other command still refuses it. `mh`'s watch loop (`mh.ps1` / `mh.sh`) checks the
  folders every 12 polls (3 s, `Test-Path` / `-d`, `_mh_present`); a change stops the server,
  the watch returns `ExitCode.REMOUNT` (6) and the loop starts it again with the new mounts,
  the tab kept (no second tab), one line said (`launcher_menu.REMOUNT`).
- Tests (`test_launcher_home.py`): bash fake docker, a folder removed during the session
  restarts the server once; a command still refuses a missing folder; the PowerShell blocks
  as text. Step 37 of `mh-measure.ps1` (by hand). Docs en + fr (`commands/home.md`).

### Not done
- The NAS checked every minute (asynchronous port 445), item 2's NAS half, and item 4 (a NAS
  asleep: time limit on reads, a *NAS not reachable* tile). **Reason:** scope of one run.
- Item 3: *Remove the USB stick* button and `mh eject E:`. **Reason:** scope.
- Item 5: files of a missing folder opened from search/browse say *not plugged in*. **Reason:** scope.
- *Also*: `mh search` in another window opening the tab on the running home server. **Reason:** scope.
- That the open tab reloads by itself after the restart (0354's `X-Media-Hygiene-Run`) is not
  re-tested here; and on WSL a stick plugged in later is not mounted at /mnt/<x> by WSL itself
  (`mh_drives.sh.j2`), so the bash follow-up works on native Linux only.
- The Windows run: `.\mh-measure.ps1 -Only 37 -Count 1 -Image media-hygiene` after
  `mh update` with the image of branch `iterate/2026-10-29`. **Reason:** Windows only.
