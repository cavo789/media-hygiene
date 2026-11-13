# 0813 — `folders` shown in the home page: host list handed to the server

- **Priority**: Medium
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh_folders.ps1.j2`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh_folders.sh.j2`, `src/media_hygiene/services/launcher_kept.py`, `src/media_hygiene/services/console_here.py`, `src/media_hygiene/cli/menu_catalog_tools.py`

Left by 0753 (from 0567): rule *visible in the web or nonexistent*. `mh folders` (`Kind.HOST`,
`web=False`) lists the photo folders, backups and quarantines, each found or not; chosen on the
home page it still prints in the terminal only.

## Why the container cannot do it alone

The home server sees only the `/data` mounts `mh` passed, and `mh` leaves out a folder whose
disk is not plugged in (0359). "Not found" is the very answer the page must give.

## What

- `mh` hands the server its configured list (photos, backups, quarantines; host paths only,
  never their contents), e.g. one environment variable or a file in the home's `/cache`, written
  at each server start (the server restarts already when a folder appears or goes, 0359).
- A `/console/folders/`-like page (same shell as `console_here`) shows each folder with its
  state: found (mounted), not found (configured, not mounted), NAS (answers or not: the host
  knows, the container does not — say "checked by mh" or pass the state too).
- `folders` gets `web=True` on the home page; typed in a terminal, unchanged.
- Docs EN + FR (`commands/folders.md` *With mh*); `docs_screenshots` should run.

## Needs maintainer

- One run of `mh` on Windows (PowerShell 5.1) to prove the hand-over; add a step to
  `tests/measure/mh-measure.ps1` if it is not visible from the page itself.

## Decided (2026-11-13, maintainer, review of feedback-2026-11-13-3-iterate)

- `mh.ps1` hands the configured folder list to the container as a small JSON file in `/cache`
  (not an environment variable: no length limit, accents and spaces kept, readable when
  debugging). Still needs one `mh` run on Windows to verify.
