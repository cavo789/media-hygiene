# 0250 — `mh`: a page left running by a closed window blocks the next one (port 8088 already allocated)

- **Priority**: High
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `tests/measure/mh-measure.ps1`

## Context

Seen by the maintainer on 2026-10-19 (mh-measure step 10c, branch `iterate/2026-10-19`):
right-click a folder → `mh --photos <folder>` → the home page (`docker run --rm -it -p
127.0.0.1:8088:8088`); the step then says "Close that mh window"; the user closes the console.
The next right-click (background of the folder, 0188) fails:
`docker: Error response from daemon: ... Bind for 127.0.0.1:8088 failed: port is already allocated`.
Then step 10's clean-up failed: `Remove-Item ... L'ete 2019 ... being used by another process`
(the leftover container still mounting the folder, *to check*: or Explorer open on it).

Closing the console kills the `docker` client, not the container (*to check* with `docker ps`):
the home page keeps serving, its mounts held, and every later `mh` page fails until Docker
Desktop restarts. Closing the window with its X is the natural user action.

## What to do

- Give each page container a known name or label (`--label media-hygiene.page=1`) so `mh` can
  find a leftover.
- Before a page run: a leftover page container whose console is gone → stop it, said in one line
  ("an mh page left open by a closed window: stopped"). Decide how to tell a leftover from a page
  open in another live window (two `mh` windows at once): e.g. the PID of the console in a label,
  checked with `Get-Process -Id`.
- Failing that, at least the "port is already allocated" message translated into one line
  saying what to do (`docker stop …`), never Docker's raw error.
- mh-measure step 10c: say "close the window with Ctrl+C, then exit", and record `docker ps`
  after the close (proves the leak and the fix).
- Tests: rendered scripts carry the label and the leftover check (bash + PowerShell).

## Acceptance

- Unit: the rendered `mh` scripts (both shells) label each page container and check for a leftover before a page run; ASCII.
- Windows (maintainer, after the work; closes the TODO, implementing needs no maintainer — as decided in the inbox of 2026-10-19): a Windows check that closing the console with its X leaves the container running (`docker ps` right after), and that the fix frees the port.

## Decided (2026-10-19)

**Stop only an orphaned page** (maintainer, review of the iterate run): each page container carries the PID of its console (a label); before a page, `mh` stops a page whose console process is gone, said in one line; a page whose console still runs is left alone and the user told to close it there. Alternative left aside: one page at a time (could cut a page in use).

## Status — PARTIAL (2026-10-19)

### Done
- Each page container is labelled `media-hygiene.page=<shell>-<PID of its console>`
  (`powershell-$PID` in mh.ps1, `bash-$$` in mh.sh); before a page, `mh` lists the
  containers publishing the page port (`docker ps --filter publish=8088`): one whose console
  is gone (`Get-Process -Id` / `ps -p`), or is this idle console, is stopped with one line
  ("An mh page left open by a closed window was stopped."); one whose console still runs is
  left alone, the user told to close it there; one without the label (an older `mh`, another
  program) is named with `docker stop <id>`. Never Docker's raw error for a container.
  Templates `mh_guards.ps1.j2` / `mh_guards.sh.j2`, texts in `services/launcher_guards.py`.
- Bash: run for real with a fake docker (stopped / live / foreign / not a page);
  PowerShell: rendered text checked, ASCII, no Add-Type, no -ExecutionPolicy in the new code.
- Troubleshooting page (en + fr): the closed window and the line said.
- Review of 2026-10-19 (2), commit a63e789: the label also holds the console's start time
  (`<shell>-<PID>-<start>`: PowerShell `(Get-Process -Id $PID).StartTime`, UTC,
  `yyyyMMddHHmmss`, invariant culture; bash field 22 of `/proc/<pid>/stat`); a page is live
  only when its PID runs AND its start time matches (a PID Windows gave again no longer
  keeps a dead page alive). An unreadable start time, or an older label without one: the
  PID alone, never a page in use cut. Bash tested with the real and a wrong start time.
- mh-measure step 10c: the window closed with its X, `docker ps` on port 8088 logged, then
  asked whether the next page said the line and opened.

### Not done
- The Windows check of the acceptance (closing with the X leaves the container; the fix frees
  the port). **Reason:** only the maintainer's Windows + Docker Desktop, with the image of this
  branch (`docker build --tag media-hygiene .`, or the PR's image), still waiting after the
  review:
  `Invoke-WebRequest https://raw.githubusercontent.com/cavo789/media-hygiene/a63e789/tests/measure/mh-measure.ps1 -OutFile .\mh-measure.ps1; Unblock-File .\mh-measure.ps1`, then `.\mh-measure.ps1 -Only 10 -Count 20`.
- A non-Docker program on port 8088 still shows Docker's raw "port is already allocated"
  (the troubleshooting page covers it). **Reason:** telling it apart needs a port probe
  before every page; not asked.

## Inbox (2026-10-19)

- A non-Docker program on 8088 → refiled as 0253 (name the program, never the raw error; maintainer).
  → stale: done by 0253, commit 12104de (inbox 2026-10-20).

### Measured (2026-10-19, step 10, `measures-20261019-2208`)
- Not checked: Avast blocked the test `mh.ps1` started by the right-click (IDP.HELU.PSD11, the
  `-ExecutionPolicy Bypass` start): the first page ended at *Run* (exit 101) with nothing taking
  over, so no leftover page existed to stop. To check again after 0257 (no Bypass) and a reboot.

## Measured on Windows (2026-10-20, step 10 of mh-measure.ps1 at e4644f4, maintainer)

- After closing the window of the right-click page with its X, a container still held 8088
  (`media-hygiene.page=powershell-14184-...`); the next right-click (background of the open folder)
  said "An mh page left open by a closed window was stopped." and opened the page, no "port is
  already allocated" (y).
- Every item done (the non-Docker program on 8088 went to 0253) → closed DONE.
