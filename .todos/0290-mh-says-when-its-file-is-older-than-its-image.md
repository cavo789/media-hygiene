# 0290 — `mh` says when its own file is older than the image it runs, and how to write it again

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/cli/templates/mh_folders.ps1.j2`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/launcher_update.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `tests/unit/` (launcher templates)

## Context

Measured on the maintainer's PC (2026-10-21, `mh-measure.ps1` step 26): the image was
rebuilt locally from the branch, but `$HOME\media-hygiene\mh.ps1` was still the file an older
image had written. What lives in `mh.ps1` (the bell and AppActivate of 0285, the minimised
shortcut of 0284, the one tab of 0280) was missing; what lives in the image (the keep-open
line) was there. The first run read "nothing works", and one conclusion drawn from it (Windows
Terminal ignores the minimised window) was wrong. `mh update` only rewrites `mh.ps1` after a
pull: with a local build it says "nothing to pull" and leaves the file as it is. A published
image is not concerned when the user runs `mh update`, but is when the image is pulled another
way (Docker Desktop, `docker pull`).

## What to do

1. `mh.ps1` / `mh.sh` carry the version (or id) of the image that wrote them (already in the
   header? check `header()`); the image knows its own.
2. At each call (one cheap comparison, like 0276's stat), when they differ: one line, e.g.
   "This mh was written by version X, the image is version Y: type mh update (or, for a local
   build, mh rewrite) to write it again with the same folders." Never blocking.
3. A local build: `mh update` (or a new `mh rewrite`, to decide) rewrites the file from the
   image as it is, with the same folders (`_mh_rewrite @(_mh_photos) @(_mh_backups)`, as step
   26 now does), instead of only saying "nothing to pull".
4. Docs (en + fr) `commands/launcher.md`; tests on the rendered scripts; `mh-measure.ps1`: a
   step with an older file then the line.

## Acceptance

- An older `mh.ps1` says so at the first call and names the command; after it, the line is gone.
- A local build rewrites the file without a pull; the folders are kept (read back).
- Whether the comparison is by version or image id: say it, and what a `latest` re-pull does.
