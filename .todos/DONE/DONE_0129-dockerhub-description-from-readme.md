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

## Status — DONE (2026-10-19, was PARTIAL)

### Earlier status — PARTIAL (2026-10-14)

### Done
- `ci.yml`, job *Publish to Docker Hub* (tags only): a checkout (`persist-credentials: false`),
  then after the manifest, `peter-evans/dockerhub-description` v5.0.0 pinned by commit SHA
  (`1b9a80c0…`), `repository: ${{ env.IMAGE }}`, `readme-filepath: ./README.md`,
  `enable-url-completion: true` (relative links and images made absolute to GitHub, at the
  tag), `short-description` read from the Dockerfile's `org.opencontainers.image.description`.
- `development.md` en + fr: the overview follows the README; the token needs read/write/delete.

### Not done
- Check that `DOCKERHUB_TOKEN` has the read/write/delete scope, and the overview after the next
  release (links, *Licences* section). **Reason:** needs the maintainer's Docker Hub account and
  a release; a token without the scope makes this last step of the job fail, after the image is
  pushed.

## Inbox (2026-10-15)

- `DOCKERHUB_TOKEN` scope: Read/Write/Delete, confirmed by the maintainer. Left: read the Docker
  Hub overview after the next release (links, *Licences* section).

## Inbox (2026-10-19)

- Docker Hub overview after v0.4.0 (published 2026-10-16), measured with the public API
  (`hub.docker.com/v2/repositories/cavo789/media-hygiene/`): `full_description` holds the README
  of v0.4.0 (15,426 characters, same headings), no relative link left (all made absolute at the
  tag, e.g. `blob/v0.4.0/LICENSE`), the *Licences* section with its table present; short
  description = the Dockerfile label. Done.
