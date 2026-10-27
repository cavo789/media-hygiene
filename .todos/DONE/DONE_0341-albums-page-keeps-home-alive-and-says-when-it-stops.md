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

## Status

**PARTIAL** (2026-10-26).

Done:
- `review/templates/presence.html.j2`: the one presence script (pings `/api/alive` every 10 s,
  `leaving` on pagehide) plus the overlay *Media Hygiene has stopped…*, shown after two failed
  pings in a row (~20 s); `window.mhEnded()` silences it when a page ends its server on purpose.
- `home_link.html.j2` includes it (every framed page and `people`); its ⌂ calls `mhEnded()`.
- `album.html.j2` includes it: home → Share → Open the albums keeps the home server alive.
- Tests in `tests/integration/test_share_album.py`; fr translated.

Left:
- A phone (`mh --lan`) does not keep the PC's server alive: `lan_app` refuses its
  `POST /api/alive` (not a network failure, so no overlay). Decide whether it should.
- The home page itself (`home_run.js.j2`, own pings), the slideshow and the TV page do not show the
  overlay yet; nor does a failed page fetch (only the pings).
- A browser test that the overlay appears once the server is gone (only the markup is tested).

## Inbox (2026-10-27)

- A phone (`mh --lan`) keeps the PC's server alive → yes, once the pairing is safe (0384, 0360): its `POST /api/alive` accepted then; with the overlay on the home page, slideshow and TV page, 0416. Closed to DONE (maintainer, 2026-10-27).
