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
