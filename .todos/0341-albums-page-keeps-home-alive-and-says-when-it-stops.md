# 0341 — The albums page keeps the home page alive, and every page says when its server stopped

- **Priority**: High — opening the albums from the home page stops Media Hygiene
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/share/templates/album.html.j2`, `src/media_hygiene/share/templates/album.js.j2`, `src/media_hygiene/share/album_page.py`, `src/media_hygiene/review/templates/home_link.html.j2`, `src/media_hygiene/review/presence.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_share_album.py`

## Context

Reported by the maintainer (2026-10-24, from the desktop shortcut): home → *Share* → *Open the
albums*. `/albums` shows *No album yet* (right), but meanwhile PowerShell prints *The home page's
tab was closed: the home page stopped* then *Home closed; your photos were not modified*. The page
stays on screen and says nothing; its ⌂ leads to *This site can't be reached*.

## Cause (read in the code)

`/albums` is served by the home server (`share/album_page.py`), in the same tab the home page
was in. The home page's presence (`review/presence.py`, `POST /api/alive`) is fed by
`home_run.js.j2` and `home_link.html.j2` only; `album.html.j2` includes neither. Leaving the
home page sends `leaving: true`, nothing pings again: after `ALIVE_SECONDS` the server ends.
Check every other page served in front of the home page the same way (the docs view `/docs/`,
the slideshow, anything `home_app.py` routes besides `/`).

## To do

1. Every page served by the home server tells its presence (the shared script, not a copy);
   the albums page opened on a **phone** (`mh --lan`) — decide whether it keeps the PC's server
   alive too (probably yes while it is shown: the user is using it).
2. Every page (all servers, not only albums): when its presence ping fails twice, or a fetch
   finds no server, the page shows the overlay *Media Hygiene has stopped: this page no longer
   answers. Open it again from the desktop shortcut / `mh`.* — instead of staying silent until
   a click. Same overlay as `homeClosed`, another text.
3. A test: the albums page pings `/api/alive`; the overlay appears once the server is gone.

## Acceptance

- [ ] Home → Share → Open the albums: the server keeps running while the tab shows the albums.
- [ ] Closing PowerShell (or Ctrl+C) while a page is open: within ~20 s the page says it stopped.
- [ ] fr strings translated (`i18n_update`).
