# 0267 — Tell when a new version exists: Docker Hub asked at most once a day, the home page and `mh menu` lead to `mh update`

- **Priority**: Medium — asked by the maintainer (2026-10-20)
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/services/update_check.py` (new), `src/media_hygiene/constants.py`, `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/cli/home_state.py`, `src/media_hygiene/review/home_views.py`, `src/media_hygiene/cli/menu_view.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_update_check.py` (new), `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `documentation/en/clean/07-configuration-file.md`, `documentation/fr/clean/07-configuration-file.md`, `.todos/PARTIAL/PARTIAL_0177-mh-update-pulls-and-rewrites.md`

## Context

`mh update` (0177) pulls the image and rewrites `mh`. Nothing tells the user when to type it.
0177 had set the rule "the tool must not look for a new version by itself".

On 2026-10-20 the maintainer asked for the check, and confirmed it once told what it changes:

- **What leaves the machine**: at most one request a day to hub.docker.com. It carries no data
  about the photos; Docker Hub sees the IP address and the repository name, as with a
  `docker pull`.
- **Without a network**: nothing is shown, nothing waits.
- **What the tool loses**: the simple rule "it contacts nothing by itself". The only other
  outside request today, Nominatim, is opt-in and comes from `places` alone.

Checked on 2026-10-20 (curl, from the devcontainer):

- `GET https://hub.docker.com/v2/namespaces/cavo789/repositories/media-hygiene/tags?page_size=25&ordering=last_updated`
  answers 200 with no account.
- Its `results` hold `name` (`latest`, `0.4.0`, …) and `digest`; `latest` and `0.4.0` shared
  the same digest.
- The headers announced `x-ratelimit-limit: 180`, with a reset 60 s after the request.
- There is no `Access-Control-Allow-Origin` header, so the browser page cannot read the answer:
  the container asks.

## What to do

1. **`services/update_check.py`.**
   - It asks the tags of the published image (`paths/docker_run.PUBLISHED_IMAGE`), keeps the
     highest `X.Y.Z` name, and compares it with the running version
     (`importlib.metadata.version`).
   - A local build (`running_image()` is not the published image) never asks.
   - At most once a day: the time and the answer are kept in `/cache` (one small JSON file next
     to the index), read again before asking.
   - A 3-second timeout; any failure (offline, a timeout, a 429, an answer it cannot read) is
     silent and leaves no traceback. The next try comes the next day.
2. **The setting.** `[general] check_updates = true` by default, with its comment in
   `config.toml.j2` (both languages through `_()`): what is sent, and how to turn it off.
3. **Where it shows.**
   - The home page: the version in the sidebar, "0.5.0 disponible" there, and a banner with
     "Voir ce qui change" (the release notes, `https://github.com/cavo789/media-hygiene/releases`,
     0187) and "Mettre à jour". The banner runs `mh update`, a host step, and the new page
     (0266) draws it from `HomeState`.
   - `mh menu`: one footer line, "A new version, 0.5.0: mh update".
   - `status` stays unchanged: it reads the tool folders only.
4. **0177.** Its "Why" gets one line: the rule changed on 2026-10-20, a daily check exists
   (this TODO).

## Acceptance

Unit (`tests/unit/test_update_check.py`), with a stand-in for the HTTP call (no network in
tests):

- a newer tag → the banner's data; the same version → nothing;
- offline, a timeout, a 429 or an answer it cannot read → nothing, no exception;
- an answer under a day old in `/cache` → no request; `check_updates = false` → no request; a
  local build → no request;
- a version written without a patch number, or a tag that is not a version (`latest`) → never
  taken for the newest.

Docs, both languages:

- the launcher page: "A new version: `mh update`" says the page tells it now;
- the configuration page: the setting and what is sent.

## Gain (estimated)

From never knowing (the image of the first day kept until a guide's command fails, 0177's
"Why") to being told the same day, with the command one click away.
