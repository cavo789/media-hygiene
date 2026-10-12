# 0118 — List the image's third-party licences, x265 (GPL) included

- **Priority**: Medium — the published image ships GPL code without saying so
- **Batch**: docker
- **Depends**: —
- **Files**: `README.md`, `README_FR.md`, `Dockerfile`, `documentation/en/development.md`, `documentation/fr/development.md`

## Context

BLOCKED 0045: `pillow-heif` wheels bundle libheif, libde265 and **x265 (GPL-2.0-or-later)**;
`pi-heif` (no x265) is discontinued. Decided in review 0056 (2026-10-12): keep `pillow-heif`
and list x265 in a licence section. The image also carries FFmpeg built from source
(LGPL with the configure flags used — check), LibRaw through `rawpy` (LGPL-2.1 / CDDL), the
GeoNames snapshot (CC BY 4.0, `geo/data/ATTRIBUTION.txt`) and Leaflet (BSD-2,
`places/static/`). The `Dockerfile` label says `org.opencontainers.image.licenses="MIT"` only.
No README section lists any of this today; the Docker Hub overview is written from the README.

## What to do

1. List the bundled native components and their licences from the built image (`pip show`,
   the wheels' `.libs`, FFmpeg's `configure` flags: no `--enable-gpl` means LGPL).
2. A short "Licences" section at the end of `README.md` / `README_FR.md`: the tool is MIT; the
   image also contains … (one line each, with a link); x265 makes the **image as a whole**
   subject to the GPL for redistribution; the sources are those of the pinned upstream releases.
3. `org.opencontainers.image.licenses`: an SPDX expression for the image (e.g.
   `MIT AND GPL-2.0-or-later AND LGPL-2.1-or-later AND …`), or keep `MIT` and say why in a
   comment — choose after step 1.
4. `development.md` (en + fr): when a dependency adds a native library, update the section.

## Explicit NON-goals

- Removing x265 (0045 option 2, declined).
- Legal advice beyond listing facts and linking the licences.

## Acceptance

- Both READMEs carry the section, in parity; `tests/unit/test_documentation.py` passes.
- Every native library found in step 1 appears in it.
