# 0416 — A paired phone keeps the PC's server alive; every page says when its server stopped

- **Priority**: Medium
- **Batch**: home
- **Depends**: 0384
- **Files**: `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/presence.py`, `src/media_hygiene/review/templates/presence.html.j2`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/slideshow/app.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_share_album.py`

## Why

Leftovers of 0341, decided by the maintainer (inbox, 2026-10-27).

## What

1. A paired phone (`mh --lan`) keeps the PC's server alive: `lan_app` accepts its
   `POST /api/alive` — only once 0384 is fixed (a forged `Host` must not pass for the PC).
2. The overlay *Media Hygiene has stopped…* on the home page itself (`home_run.js.j2`, own pings),
   the slideshow and the TV page; and after a failed page fetch, not only after the pings.
3. A browser test (CI Chromium, 0366) that the overlay appears once the server is gone.

## Done (2026-10-27)

- `POST /api/alive` passes from a paired phone (`lan_paths`), to the home page's `Presence`;
  the phone's home page pings it too (`wirePresence` no longer PC-only): an open phone keeps
  the server up, its "leaving" gives the usual 10 s grace.
- `presence.html.j2`: a page fetch that finds no server asks again at once (overlay after
  two failures in a row, as the pings); `presence_probe` (the slideshow's remote: `HEAD` of
  itself, any answer = up, never "leaving"); `presence_es5` (the TV page: the overlay, and an
  ES5 `XMLHttpRequest` probe in `screen.js.j2`). The home page keeps its own `#stoppedDlg`,
  shown after its pings or any failed fetch (already so; now on the phone too).
- Browser test: `pages_walk.py` ends by stopping the server behind the search page's back and
  waits for `#mhStopped` (CI Chromium, `test_pages_browser.py`).
