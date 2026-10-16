# 0177 — `mh update`: pull the new image, rewrite `mh` with the same folders

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: 0176
- **Files**: `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `src/media_hygiene/services/launcher.py`, `src/media_hygiene/services/launcher_menu.py`, `src/media_hygiene/cli/menu_catalog.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/{en,fr}/commands/launcher.md`, `documentation/{en,fr}/clean/quick-guide.md`, `documentation/{en,fr}/reference-troubleshooting.md`, `tests/unit/test_launcher_folders.py`
- **Needs maintainer**: one run on Windows: `mh update` with an older image pulled first (PowerShell 5.1)

## Why

A user never types `docker pull`: they keep the image of their first day, its bugs and its old
`mh`, without knowing it. The tool must not look for a new version by itself: a request at each
run would break "nothing leaves the machine" (`geo/`, README). So the update is a command the
user types, and the documentation says when.

## What to do

- `mh update`, handled by `mh` itself: `docker pull <image>` (the image written in the script;
  a local build `media-hygiene` has nothing to pull: say so and stop), then rewrite `mh` exactly
  as `mh folders` does (0176: the kept `launcher` arguments, temporary file, replaced only on
  success, reloaded), then show the version: `mh --version` of the new image, before → after
  when they differ, "already the latest" when the pull changed nothing.
- `docker pull` output: shown as it is (its progress bars are what a user expects).
- Old images: say once how much space the previous one still takes and the command freeing it
  (`docker image prune`), never run it unasked.
- In the menu: one line under the menu ("Update: mh update"), not a step.
- Documentation: when to type it (the release notes link, "once a month or when the guide
  shows a command your mh does not know").

## Acceptance

- Unit: bash `mh update` with a fake `docker` (pull, run launcher, --version) → pull called with
  the script's image, script replaced and reloaded, versions shown; a failed pull leaves `mh`
  intact; the local image → said, nothing pulled. PowerShell text ASCII.
- Docs both languages: the launcher page, "Clean in short" (later section), troubleshooting
  ("a command the guide shows is unknown" → `mh update`).

## Gain (estimated)

Updating: `docker pull` + the long `launcher` line retyped (both unknown to a newcomer) → one
command.

## Status — PARTIAL (2026-10-16)

### Done
- `mh update` (`_mh_update` in `mh_folders.{ps1,sh}.j2`): image id and `--version` before,
  `docker pull <the script's image>` with its own output, then the same rewrite as `mh folders`
  (temporary file, replaced only on success, reloaded, folders read back), `--version` after:
  "Updated: before → after", or "Already the latest version" when the id did not change; the
  previous image's size and `docker image prune` said, never run. A failed pull leaves `mh` as
  it was. A local build (`MEDIA_HYGIENE_IMAGE` set: the image is not `cavo789/media-hygiene`):
  said, nothing pulled. Never runs by itself.
- Menu line (shared with 0176); docs en/fr: launcher page ("A new version: `mh update`", when
  to type it), "Clean in short" step 12, troubleshooting ("A command the guide shows is
  unknown").
- Tests: bash with a fake `docker` (pull with the script's image, rewrite, versions, space line,
  failed pull, latest, local build); PowerShell text (pull only for the published image).
- `tests/measure/mh-measure.ps1` step 11e.

### Not done
- The Windows run: `mh update` with an older image pulled first (PowerShell 5.1).
  **Reason:** no PowerShell here, and no published image with `mh update` yet; step 11e
  (`powershell -ExecutionPolicy Bypass -File .\mh-measure.ps1 -Only 11 -Count 20`) tags the local
  build as `cavo789/media-hygiene` (asks first) and lets `mh update` pull the published one.
- No release notes exist (CI publishes tags to Docker Hub, no GitHub Release): the docs link the
  Docker Hub tags page instead. **Reason:** a decision for the maintainer.
  → refiled as 0187: CI creates a GitHub Release (maintainer, inbox 2026-10-16).

### Measured on Windows (2026-10-16, step 11e of mh-measure.ps1)
- Local build: "This image is a local build: nothing to pull." as designed.
- Real update (local build tagged `cavo789/media-hygiene`, then pulled): the published image is
  v0.3.0, which has no `launcher` command ("No such command 'launcher'"): `mh update` said
  "mh is unchanged: launcher refused it" and `mh.ps1` kept its folder — safe. The full path
  (pull, rewrite, both versions said) can only be measured once a release with `launcher` is
  published: rerun step 11 then.
