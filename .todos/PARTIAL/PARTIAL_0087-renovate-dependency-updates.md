# 0087 — Keep pinned versions up to date with Renovate

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: TBD

## Context

Versions are pinned in several places that nothing tracks today: GitHub Actions by SHA with a
`# vX.Y.Z` comment (`.github/workflows/ci.yml`), `uv.lock` / `pyproject.toml`, the Python base
image by digest and tool versions in `ARG`s of the `Dockerfile` (`PYTHON_IMAGE`, `UV_VERSION`,
`FFMPEG_VERSION`), and pre-commit hooks in the non-standard `.config/.pre-commit-config.yaml`.
Renovate is preferred over Dependabot because it can update `ARG` values through annotated
custom (regex) managers and lets us point it at the pre-commit file under `.config/`.

## Acceptance

- [ ] `renovate.json` (or `.github/renovate.json`) at the repository root, Renovate GitHub App
      installed on `cavo789/media-hygiene` (or a self-hosted workflow, choice documented).
- [ ] Managers cover: GitHub Actions (SHA + version comment kept), `uv` (`pyproject.toml` +
      `uv.lock`), Dockerfile base image digest, pre-commit hooks in `.config/.pre-commit-config.yaml`.
- [ ] Each version `ARG` in the `Dockerfile` carries a `# renovate: datasource=… depName=…`
      annotation, matched by a custom regex manager (`PYTHON_IMAGE`, `UV_VERSION`, `FFMPEG_VERSION`).
- [ ] `FFMPEG_SHA256` handled: either a documented manual step on ffmpeg PRs or a small workflow
      that recomputes the checksum on the Renovate branch.
- [ ] Updates grouped (e.g. actions / python / docker / pre-commit) on a weekly schedule, so a
      single run doesn't trigger many CI builds; Dependency Dashboard issue enabled.
- [ ] No automerge to `main` at first (a push to `main` rebuilds the Docker image).
- [ ] Config validated (`renovate-config-validator`) and the first onboarding PR reviewed.
- [ ] Developer page updated in both languages (`documentation/en/` and `documentation/fr/`)
      to mention Renovate next to the `deps` helper.

## Status — PARTIAL (2026-10-11)

### Done
- `.github/renovate.json`: `config:recommended`, Dependency Dashboard, `helpers:pinGitHubActionDigests`
  (SHA + `# vX.Y.Z` comment kept), `pep621` (pyproject + uv.lock, weekly lock maintenance),
  `pre-commit` enabled on `.config/.pre-commit-config.yaml`, one custom regex manager for the
  annotated `Dockerfile` ARGs; four groups (GitHub Actions, Python dependencies, Docker images
  and tools, pre-commit hooks) on `before 6am on monday` (Europe/Brussels); no automerge.
  Python base image: only digest updates (a new Python minor stays a deliberate change).
- Choice documented: the Renovate GitHub App (not a self-hosted workflow).
- `Dockerfile`: `# renovate:` annotations on `PYTHON_IMAGE` (docker `python`, tag + digest),
  `UV_VERSION` (docker `ghcr.io/astral-sh/uv`), `FFMPEG_VERSION` (github-tags `FFmpeg/FFmpeg`,
  `n<version>` stripped by `extractVersion`). Regex checked to match all three.
- `FFMPEG_SHA256`: documented manual step (Dockerfile comment, a `prBodyNotes` reminder in every
  FFmpeg PR, developer page); `ADD --checksum` makes the build fail until it is updated.
- `renovate-config-validator --strict` passes (repository mode).
- Developer page updated in `documentation/en/` and `documentation/fr/` next to `deps`.

- Renovate GitHub App installed on `cavo789/media-hygiene` by the maintainer (2026-10-11).

### Not done
- Review Renovate's first run once `sortering` is merged into `main` (Renovate reads its config
  from the default branch). Check the Dependency Dashboard lists three `custom.regex` deps from
  the Dockerfile, the pre-commit hooks, the actions and the pep621 deps. If an onboarding PR was
  opened before the merge (it proposes its own `renovate.json`), close it without merging.
  **Reason:** the merge into `main` is postponed by the maintainer (a push to `main` rebuilds the
  image).
