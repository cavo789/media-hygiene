# 0442 — Back to the home page in under a second (phone and PC)

- **Priority**: High
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/review/templates/splash.html.j2`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/review/serving.py`, `src/media_hygiene/review/http.py`

## Why

The maintainer, 2026-10-27, on the phone (HTTPS, 0430): *Back* or *⌂ Back to home* shows the
splash again for several seconds; the home page should be back in under a second.
Likely causes (estimated, to measure first: skill `measure-before-ranking`):
1. the splash stays until `GET /api/state` answers, which reads the tool folders through
   Docker Desktop (0277);
2. one request per connection (`http.py`: no keep-alive): over TLS, a handshake for every
   request of the page (page, assets, each call).

## What

- Measure both on the demo tree (time to `/api/state`, handshakes per page load).
- Draw the last state at once (kept in `sessionStorage`, per viewer convenience), the splash
  only on a first load; refresh it from `/api/state` behind, marked as "updating".
- If the handshakes weigh: keep-alive for the home network's door (a few requests per
  connection, an idle timeout), or HTTP caching of the assets (`max_age` already exists).
- Say before → after, measured.

## Explicit NON-goals

- A service worker cache of API answers (the phone app caches the offline page only, 0432).

## Measured before the change (maintainer, 2026-11-03, phone on the home Wi-Fi, image 32cafce7)

From the search page back to home, stopwatch, splash (meerkat) shown **every time**:

| Way | 1 | 2 | 3 | Mean |
|---|---|---|---|---|
| *⌂ Back to home* | 8.15 s | 8.63 s | 8.91 s | 8.6 s |
| Phone's *Back* | 8.22 s | 8.66 s | 8.56 s | 8.5 s |

Goal: under 1 s (≈ −90 %). Both ways cost the same: the cost is the home page's load, not the
navigation. Next: measure here (demo tree) where the 8 s go (`/api/state`, TLS handshakes per
request), then the same timing by the maintainer after the change.
