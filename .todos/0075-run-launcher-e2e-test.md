# 0075 — Run the `mh` launcher e2e test against the real image

- **Priority**: Medium
- **Batch**: guidance
- **Depends**: —
- **Files**: `tests/e2e/test_launcher_image.py`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/cli/templates/mh.sh.j2`

## Context

TODO 0060 added `media-hygiene launcher` and the `mh` shell function, with
`tests/e2e/test_launcher_image.py`: it generates the script from the image with named volumes,
swaps the published image name for the local one and runs `mh audit` in bash with
`HOME=tmp_path`. The test was written during an unattended night run where e2e was forbidden, so
it has never been executed.

The PowerShell side was checked by hand on 2026-10-11: the user generated
`$HOME\media-hygiene\mh.ps1` with the published image. Loading it and running `mh` commands is
covered by the manual checks of TODO 0060, not by this TODO.

## Steps

- [ ] With the machine otherwise idle (heavy step, run alone): `e2e` (builds
  `media-hygiene:latest`, then `pytest -m e2e`; log in `/tmp/media-hygiene/e2e.log`).
- [ ] If `test_launcher_image.py` fails, fix the launcher or the test; keep the log for review.
- [ ] Check that the other e2e tests still pass with the launcher changes (console on stderr for
  `DATA_COMMANDS`, `MEDIA_HYGIENE_LAUNCHER`).

## Acceptance

- `tests/e2e/test_launcher_image.py` passes against a freshly built image.
- The whole e2e suite is green.
