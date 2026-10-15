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
