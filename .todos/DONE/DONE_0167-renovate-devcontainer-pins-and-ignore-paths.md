# 0167 — Renovate: follow the devcontainer's `GH_VERSION`, ignore `.claude/`

- **Priority**: Low
- **Batch**: docker
- **Depends**: —
- **Files**: `.github/renovate.json`, `.devcontainer/Dockerfile`

## Context

Follows 0087 (closed DONE on 2026-10-15). The first Dependency Dashboard
(cavo789/media-hygiene#3, read with `gh` on 2026-10-15) lists every pin of the image's
`Dockerfile` (4 annotated ARGs: `python`, `ghcr.io/astral-sh/uv`, `FFmpeg/FFmpeg`,
`qarmin/czkawka`), the GitHub Actions, the pep621 dependencies and the two remote pre-commit
hooks. Two gaps:

1. `.devcontainer/Dockerfile`: the `dockerfile` manager finds the `FROM` images through their
   ARG defaults (`python`, `uv`, `mwader/static-ffmpeg`), but `ARG GH_VERSION=2.101.0` (the
   `gh` CLI) is not followed: nothing annotates it.
2. `.claude/agents/dockerfile-best-practices-reviewer.md` is listed as a Dockerfile (no
   dependency found): noise in the dashboard.

## What to do

1. Annotate `GH_VERSION` with `# renovate: datasource=github-releases depName=cli/cli`, and
   extend the custom regex manager's `managerFilePatterns` to `.devcontainer/Dockerfile` if the
   current pattern (`(^|/)Dockerfile$`) does not already reach it (to check: it should); a
   `v` prefix of the release tags may need `extractVersion`.
2. `"ignorePaths"` gets `.claude/**` (keep `config:recommended`'s defaults: an `ignorePaths`
   replaces them, to check in the Renovate docs).
3. `renovate-config-validator --strict`, then tick "run again" on the dashboard and check both.

## Acceptance

- The dashboard lists `cli/cli` under `.devcontainer/Dockerfile`, and no `.claude/` file.

## Status — PARTIAL (2026-10-15)

### Done
- `GH_VERSION` of `.devcontainer/Dockerfile` annotated (`# renovate: datasource=github-releases depName=cli/cli`); the custom manager's `(^|/)Dockerfile$` already reached it. Regex tested in Python on both Dockerfiles: 4 matches in the root one (unchanged), `cli/cli` 2.101.0 in the devcontainer one.
- `cli/cli` tags carry a `v` prefix (`gh release list -R cli/cli`: v2.102.0), unlike `qarmin/czkawka`: a `packageRules` entry with `extractVersion` `^v(?<version>.+)$` keeps `GH_VERSION` bare.
- `ignorePaths` gets `.claude/**`; the Renovate docs list `ignorePaths` as not mergeable, and `config:recommended` extends `:ignoreModulesAndTests`, so the preset's 8 globs are repeated explicitly.

### Not done
- `renovate-config-validator --strict`: `npx` is absent in the devcontainer (run it where Node exists).
- Dashboard check (tick "run again" on cavo789/media-hygiene#3: `cli/cli` under `.devcontainer/Dockerfile`, no `.claude/` file).
  **Reason:** Renovate reads `main`; possible only after this branch is merged.

## Status — DONE (2026-10-15)

Checked after PR #7 was merged, on the Dependency Dashboard (cavo789/media-hygiene#3, read with
`gh issue view 3` on 2026-10-15, updated by Renovate at 12:51 UTC):

- `cli/cli` is listed under `.devcontainer/Dockerfile` (custom regex manager), and no
  `.claude/` file appears anywhere in *Detected Dependencies*.
- End to end: Renovate opened PR #8 `chore(deps): update dependency cli/cli to v2.102.0`, merged
  (`GH_VERSION=2.102.0` on `main`): the annotation and the `v`-stripping `extractVersion` work.
- `renovate-config-validator` never ran locally, but Renovate applied the new config without
  opening a configuration-error issue: no further check needed.
- The "run again" checkbox (`<!-- manual job -->`) sits at the very bottom of the dashboard,
  after *Detected Dependencies*; it was not needed, Renovate ran on its own after the merge.
