# 0108 — Native Linux: document `/data$HOME/…` everywhere, and check the commands the tool builds

- **Priority**: Medium — the guides only know Windows and WSL
- **Batch**: mounts
- **Depends**: —
- **Files**: `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`, `documentation/en/reference-mount-points.md`, `documentation/fr/reference-mount-points.md`, `src/media_hygiene/paths/`, `src/media_hygiene/services/next_command.py`, `src/media_hygiene/services/launcher.py`, `tests/e2e/`

## Context

UX review of 2026-10-12. Every guide writes Windows paths, then WSL paths (`/mnt/c/Photos` →
`/data/c/Photos`). A Linux desktop user with `~/Pictures` and a USB disk under
`/media/<you>/Disk` finds no rule for the target of `-v`: `reference-mount-points.md` only gives
`/data/<drive>/<path>`, and nothing names Linux. The new page *Install Docker*
(`start/00-install-docker.md`) suggests mirroring the path, `-v "$HOME/Pictures:/data$HOME/Pictures:ro"`:
checked from sources, the audit then shows `/home/<you>/Pictures/…`, the real path. Not
checked on a native Linux Docker engine:

- the 👉 *What next* command and the `launcher` script rebuild the host side of each mount from
  the mount table; on a native engine the bind source may be read differently than under Docker
  Desktop (WSL `/mnt/c`);
- a folder under `/media` (another file system): its mountinfo root is relative to that disk.

## Goal

- An e2e case (or a manual check, recorded) on a native Linux engine: `audit` of `$HOME/x` and of
  a second file system, then the 👉 command and `launcher --shell bash` reproduce the same `-v`.
- Step 3 gets a *From Linux* paragraph next to *From WSL*; the mount points page states the rule
  (`/data` + the full path; `X:\` → `/data/x` for Windows).

## Acceptance

- The rule is in both languages; the check is recorded in the TODO or covered by a test.

## Status — PARTIAL (2026-10-13)

### Done
- Found from the code: on a native engine, the 👉 command and `launcher` rebuilt the host side of
  a data mount from mountinfo's root, which is relative to *its* file system: `/me/Pictures`
  when `/home` is a partition of its own, `/` for a disk under `/media`. Fixed:
  `paths/host_folders.bind_source` keeps the naming convention (`/data/home/me/Pictures` →
  `/home/me/Pictures`) when the mount table's folder is only its end; a Windows folder, a named
  volume, or a folder mounted off-convention (`-v ~/Pictures:/data/pictures`) is kept as found.
  Tests: `tests/unit/test_next_command_linux.py` (root fs, `/home` partition, USB disk, free
  mount point).
- Docs en + fr: *From Linux* in `start/03-several-folders.md` (`$HOME/Pictures:/data$HOME/…`,
  `/media/$USER/…`), the rule in `reference-mount-points.md`, `mh` "From WSL or Linux".

### Not done
- The check on a native Linux Docker engine (`audit` of `$HOME/x` and of a second file system,
  then the 👉 command and `launcher --shell bash`).
  **Reason:** the devcontainer's engine is Docker Desktop (WSL2); needs a Linux machine.
  Known limit: a disk mounted *below* its root and off-convention
  (`-v /media/me/Disk/Photos:/data/media/me/Disk`) still shows `/Photos`: the mount table
  cannot tell where the disk is mounted on the host.
