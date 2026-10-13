# 0129 — Docker Hub overview: published from README.md by CI at each release

- **Priority**: Low — the licences section (0118) is on GitHub only
- **Batch**: docker
- **Depends**: —
- **Files**: `.github/workflows/ci.yml`, `README.md`, `documentation/en/development.md`, `documentation/fr/development.md`

## Context

Review of the 2026-10-13 run (0118): the READMEs now end with a *Licences* section (x265 makes the
image as a whole GPL for redistribution). `ci.yml` builds and pushes the image on a `vX.Y.Z` tag
(`docker/login-action`, `docker/build-push-action`) but nothing updates the Docker Hub overview:
it is maintained by hand and does not carry the section. Decided with the maintainer: let CI
publish `README.md` as the overview at each release.

## What to do

1. In `ci.yml`, after the multi-arch manifest is pushed on a tag, a step that sends `README.md`
   to the Docker Hub repository description (e.g. `peter-evans/dockerhub-description`, pinned by
   commit SHA like the other actions, with `short-description` from the `Dockerfile`'s
   `org.opencontainers.image.description`). Same `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` secrets;
   check the token's scope allows editing the description (read/write/delete).
2. Links: Docker Hub renders Markdown but resolves relative links against nothing — check the
   README's relative links (`documentation/…`, `LICENSE`) and make them absolute GitHub URLs, or
   let the action's option rewrite them, so they work on both sites.
3. `development.md` (en + fr), *Continuous integration and releases*: the overview follows the
   README; edit the README, not Docker Hub.

## Explicit NON-goals

- `README_FR.md` on Docker Hub (one overview only: the English one).

## Acceptance

- After the next release, the Docker Hub overview equals `README.md`, the *Licences* section
  included, its links working.
