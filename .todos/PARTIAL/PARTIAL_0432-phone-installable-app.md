# 0432 — The home page installs as an app: manifest, service worker, offline meerkat, shared splash

- **Priority**: Medium
- **Batch**: phone
- **Depends**: 0430, 0431
- **Files**: `src/media_hygiene/review/lan_paths.py`, `src/media_hygiene/review/home_assets.py`, `src/media_hygiene/review/templates/` (home page head, a new shared splash template, the offline page), `src/media_hygiene/assets/images/meerkat-asleep.webp`, `src/media_hygiene/assets/images/meerkat-splash.webp`, `documentation/en/`, `documentation/fr/`
- **Needs maintainer**: a test on the maintainer's Android phone and on an iPhone (install invitation, icon, offline page)

## Goal

Points 5–7 of the design approved on 2026-10-27 (split from 0430, which has the full design):

- `manifest.webmanifest` (name "Media Hygiene" / « Média Hygiène », meerkat icon,
  `display: standalone`, `start_url: /`, `background_color`), `apple-touch-icon`,
  `apple-mobile-web-app-*` and `apple-touch-startup-image` tags; on iOS Safari not
  standalone, a one-line hint (Share > Add to Home Screen).
- A service worker caching only the offline page and its meerkat (never photos, never API
  answers: memory `phone-read-only`); on a failed navigation it shows "Media Hygiene is
  asleep: it is not running on the PC. On the PC, start Media Hygiene (`mh`)", with Retry,
  retrying every few seconds.
- Every phone-facing text says "Media Hygiene", never the bare `mh` (except where typed).
- One splash (meerkat-splash.webp + "Media Hygiene" + one line of what it does, the words
  written by the page), one shared template for the phone app's launch and the PC's home
  page while it loads.

## Tests

The manifest and service worker served with the right types and reachable by a paired
phone (`lan_paths`); the service worker caches nothing but the offline page and its
picture; the splash template is the same on both pages.

## Explicit NON-goals

- HTTPS and the CA (0430), durable pairing (0431).

## Status — PARTIAL (2026-10-27)

### Done
- `review/app_shell.py`: `/manifest.webmanifest` (name "Media Hygiene" / « Média Hygiène »,
  standalone, `start_url /`, background colour, icons), `/app-icon-192.png` and `-512.png`
  (made from `meerkat-splash.webp` with Pillow, cached), `/sw.js`, `/offline`,
  `/offline-meerkat.webp`; served by the home network's door before pairing (Chrome fetches
  a manifest without cookies; none holds anything private).
- `templates/app_worker.js.j2`: caches only the offline page and its meerkat; a failed
  navigation shows the offline page; every other request passes through.
- `templates/app_offline.html.j2`: "Media Hygiene is asleep", Retry, a `HEAD /` every 5 s.
- `home.html.j2` (phone only): manifest, `apple-touch-icon`, `apple-touch-startup-image`,
  `apple-mobile-web-app-*` tags; `home.js.j2` registers the worker and shows the iOS line
  (Share > Add to Home Screen) in Safari when not standalone.
- `templates/splash.html.j2`: one startup screen (meerkat-splash + "Media Hygiene" + one
  line) included by the home page, so PC and phone are identical.
- CSP: `manifest-src 'self'; worker-src 'self'` (`default-src 'none'` blocked both).
- The pairing page says "Media Hygiene", not the bare `mh`.
- `lan_response` moved to `review/lan_card.py` (`lan_app.py` at the cap).
- Docs en+fr (`commands/home.md` "Media Hygiene as an app on the phone"), translations,
  `tests/unit/test_app_shell.py`.

### Not done
- The test on the maintainer's Android phone and an iPhone: install invitation, icon,
  splash, offline page with the PC's `mh` stopped.
  **Reason:** needs the maintainer's phones.
- iOS startup images per screen size (`apple-touch-startup-image` with `media` queries):
  one 512 px image is given for now.
  **Reason:** to add only if the iPhone test shows a blank launch.
- `docs_screenshots` (the splash changed on the PC's home page).
  **Reason:** heavy (image build + browser): run by the maintainer.
