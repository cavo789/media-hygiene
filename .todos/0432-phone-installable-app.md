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
