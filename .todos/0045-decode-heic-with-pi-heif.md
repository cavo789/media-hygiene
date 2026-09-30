# 0045 — Decode HEIC with `pi-heif` instead of `pillow-heif`: no x265 (GPL) in the image, about 22 MB less

- **Priority**: Medium — ideally before the 0.3.0 release, so that no published `media-hygiene` image ships x265
- **Batch**: dependencies
- **Depends**: —
- **Files**: `pyproject.toml`, `uv.lock`, `src/media_hygiene/scan/image_check.py`, `tests/support/media.py`, `tests/support/docs/shots.py`, `tests/unit/test_image_metadata.py`

## Context

The tool only **decodes** HEIC: `prepare_image_worker` (`scan/image_check.py`) calls
`pillow_heif.register_heif_opener()`, nothing else. But the `pillow-heif` wheel also bundles the
HEVC **encoder**:

- `pillow_heif.libs` is 26 MB: libheif and libde265 (LGPL-3.0), and libx265 (GPL-2.0-or-later),
  most of the weight;
- x265 is the only GPL library loaded into the tool's process. (The Debian base image holds GPL
  programs such as bash and apt: mere aggregation, as in any Debian image. rawpy's LibRaw is
  built without its GPL demosaic packs: `rawpy.flags` says so.)

[`pi-heif`](https://pypi.org/project/pi-heif/), by the same author, is the decoding-only
variant (BSD-3-Clause):

- its 1.4.0 wheel for cp314 x86_64 is 1.5 MB and bundles libheif and libde265 only (3.8 MB
  unpacked); cp314 wheels exist for manylinux x86_64 and aarch64 (the image's two platforms);
- `pi_heif.register_heif_opener()` exists, same API.

Trade-off: `pi-heif` releases lag behind. 1.4.0 (2026-06-10) bundles libheif 1.23.0;
`pillow-heif` 1.8.0 (2026-09-22) bundles 1.23.4. libheif parses untrusted files: read the libheif
changelog between those versions for security fixes before switching, and watch the release
cadence afterwards.

The tests and the documentation screenshots **write** HEIC files
(`pillow_heif.from_pillow(picture).save(...)` in `tests/support/media.py` and
`tests/support/docs/shots.py`): they still need the encoder.

## Proposal

- Runtime dependency `pi-heif`; `pillow-heif` moves to the `dev` group, only to write HEIC
  fixtures. `uv lock`.
- `image_check.py`: `import pi_heif` and `pi_heif.register_heif_opener()`.
- Both packages then live in the dev venv, each with its own copy of libheif (auditwheel renames
  them, no clash). A test must prove the tool decodes with `pi-heif` alone: in a fresh
  subprocess, import the scan modules, decode and describe a HEIC fixture, and check that
  `pillow_heif` is not in `sys.modules`.
- HEIC metadata recorded since 0025 (format `HEIF`, EXIF date, camera, GPS) must come out the
  same: `test_image_metadata.py` already covers HEIF, keep it green.
- Rebuild the image: compare its size before and after (`dive`, `dive_ci` gate), run `e2e`.

## Acceptance

- [ ] `uv tree --no-dev` has no `pillow-heif`; the image holds no `libx265*` file
  (`find / -name 'libx265*'` in the image finds nothing).
- [ ] HEIC files are decoded and described as before (unit and integration tests, `e2e`).
- [ ] The test above proves `pillow_heif` is never imported by the tool.
- [ ] The libheif changelog between 1.23.0 and the version `pi-heif` bundles has been read; any
  missing security fix is written down in the commit message.
- [ ] Image size before and after written down in the commit message.
- [ ] Maintainer, by hand: in the Docker Hub description's *License* section, x265 (GPL-2.0+)
  is removed from the list of bundled components.
