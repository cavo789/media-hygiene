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
