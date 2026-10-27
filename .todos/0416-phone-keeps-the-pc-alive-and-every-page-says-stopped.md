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
