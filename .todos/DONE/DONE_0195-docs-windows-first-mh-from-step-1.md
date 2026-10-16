# 0195 — Docs Windows-first: `mh` written at step 1, `docker run` folded away

- **Priority**: High
- **Batch**: docs
- **Depends**: —
- **Files**: `README.md`, `README_FR.md`, `documentation/en/start/00-install-docker.md`, `documentation/fr/start/00-install-docker.md`, `documentation/en/start/01-first-audit.md`, `documentation/fr/start/01-first-audit.md`, `documentation/en/start/02-keep-the-cache.md`, `documentation/fr/start/02-keep-the-cache.md`, `documentation/en/start/03-several-folders.md`, `documentation/fr/start/03-several-folders.md`, `documentation/en/README.md`, `documentation/fr/README.md`, `tests/support/docs/`, `.config/mkdocs/mkdocs.yml`

## Why

Asked by the maintainer (2026-10-16): a Windows reader of the step-by-step guide meets `mh`
only at the end of step 3 (`start/03-several-folders.md`, "Write your folders once"), after
three steps of long `docker run` commands; the README's quick start also opens on a
`docker run … audit`. The short guides (*Clean / Sort / Find in short*) already start with
"0. Once: write the `mh` command". The step-by-step order (minimal `docker run`, then the
cache, then several folders) predates `mh`, which now does what steps 2 and 3 teach by hand
(the cache volume, the `-v` per folder, `:ro` per command, the time zone).

Decided (maintainer, 2026-10-16, "Windows d'abord"): after installing Docker, step 1 writes
`mh` and runs `mh audit`; the raw `docker run` lines move to folded boxes.

## What

- `start/00-install-docker.md`: ends on one line pointing to step 1 (write `mh`).
- `start/01-first-audit.md`: the execution policy line, the `launcher --photos` lines and the
  profile line (the same as *Clean in short*, step 0: one source of truth, reuse or link it),
  then `mh audit` and how to read its result (the rest of the page stays). A folded
  `??? note "Without mh, from WSL or Linux"` holds today's `docker run` and its explanation
  (`-v`, `:ro`).
- `start/02-keep-the-cache.md`: `mh` keeps the cache by itself; the page becomes what the cache
  gives (minutes → seconds, measured figures already there) with the `docker run` form folded.
  Merge into step 1 if little is left (then renumber, keep the old URLs reachable: mkdocs
  redirects or a short page).
- `start/03-several-folders.md`: `mh folders add` first; the `-v` per folder, WSL and Linux
  sections folded or moved after.
- `README.md` / `README_FR.md` quick start: PowerShell `mh` lines first (with `mh shortcut`),
  the one-line `docker run … audit` kept as "just try it" for WSL/Linux or a test.
- Both languages, same structure; the 🤖 and Windows-first rules of the project apply.
- Captures: the console blocks of these pages become `mh` runs where `tests/support/docs/`
  can render them (`<!-- capture: … -->`); say that `docs_screenshots` must run.

## Acceptance

- `tests/unit/test_documentation.py` (links, anchors, parity), `tests/unit/test_docs_site.py`
  (mkdocs nav, strict build) green.
- A Windows reader goes Docker → step 1 → `mh audit` without meeting a `-v`.

## Gain (estimated)

The Windows newcomer types one setup block, then `mh audit`, instead of three steps of
`docker run` lines (~90 characters + 30 per folder each, estimated from the current pages)
before discovering `mh`.
