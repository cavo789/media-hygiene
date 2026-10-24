# 0293 — A family landing page for the photo library, on the home network

- **Priority**: Low — an idea of the maintainer (2026-10-21), after 0269 and 0291
- **Batch**: home
- **Depends**: 0269, 0291, 0297
- **Files**: `src/media_hygiene/search/app.py`, `src/media_hygiene/search/views.py`, `src/media_hygiene/search/days.py`, `src/media_hygiene/search/templates/`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/config/`, `documentation/en/`, `documentation/fr/`

## Context

The maintainer asked Google Gemini for a home page for the address the PC serves on the home
network (`http://<PC LAN address>:8088/`, the port of the 0291 test) and pasted its answer
(2026-10-21) as a lead, not a design. Gemini's page is a generic "homelab" dashboard: a welcome
banner with a clock and the weather, six service cards (cloud, photos, Plex, home automation,
chat, monitoring) each with a pulsing "online" dot, hand-written family announcements, gauges
(NAS storage, CPU, bandwidth), a particle animation, a light/dark switch.

The approved home page (mockup of 2026-10-20: 5-stage cycle, avonture.be look, the meerkat) is
the **maintainer's** page: import, clean, sort, find, back up. Once 0269 opens pages to the
LAN, the family (a phone on the sofa, the TV through the Chromecast, 0291) needs another door:
**read-only**, no cleaning or sorting step in sight, the photos first.

## What to keep from Gemini's page, made true

Every block of Gemini's page shows invented figures; kept only where the index gives the fact:

| Gemini | Here |
|---|---|
| Welcome banner + weather | **"On this day"**: photos taken on today's date in earlier years (the search already reads every date form as a day, `search/days.py`, `media_day`), one large picture and "2019 · 2016 · 2012" to switch years |
| Service cards with an "online" dot | Three to four entrances: **Slideshow on the TV** (0291), **Search** (dates, places, people), **Map** (places), **Latest additions**; no status dot (the page answers, so the service is up) |
| Family announcements (typed by hand, lost at reload) | **Latest additions**, computed: the last imported or sorted events (folder, date range, count, a few thumbnails) |
| Storage / CPU / bandwidth gauges | At most one line of real facts: number of photos and videos, years covered, last audit date (from the index); no CPU or network |
| Light/dark switch | Already decided for the home page (Auto/Clair/Sombre): the same |

## What not to take

- Tailwind, Font Awesome and Google Fonts from CDNs: the served pages are offline, under a CSP,
  and follow the avonture.be design system already chosen.
- The particle canvas (a `requestAnimationFrame` loop that never stops: battery on a phone, CPU
  on the TV) and the clock ticking every second.
- The family name in the page or in the repository (public repo): a title setting instead.
- Announcements typed into the page: a write path for every visitor, outside "read-only first"
  (0269 decision 3).

## Decisions for the maintainer

1. **One page or two.** A family landing page apart from the maintainer's home (chosen by the
   pairing: a family device lands here, the PC on the cycle), or one home where the acting
   stages are hidden from a paired phone. What two pages cost: a second layout to keep in step.
2. **What the family sees.** The four entrances above, or fewer (e.g. only "On this day" and the
   slideshow).
3. **The title.** A setting (`[home] family_title`, empty by default: "Our photos" /
   "Nos photos"), never a name in the repository.

## Decided (2026-10-23)

By the maintainer, at the start of `/todo:iterate`:

1. **One page**: the home page itself, its acting stages (import, clean, sort, back up and the
   tools that change files) hidden from a paired phone — not a second page. The PC keeps the
   whole cycle.
2. **What the family sees**: all four entrances — *On this day*, *Slideshow on the TV*,
   *Search*, *Map* and *Latest additions*.
3. **The title**: the setting as proposed (`[home] family_title`, empty by default: "Our
   photos" / "Nos photos"), never a name in the repository.

## Acceptance

To write once decided. At least: a phone paired by 0269 opens the page and sees today's
memories from the index, every figure on the page comes from the index (no placeholder), the
page holds no external resource and no endless animation.

## Decided (2026-10-22, by the maintainer, `/todo:iterate`) — moved to 0334

The link that opens one album only, for other people's phones (no pairing), is now its own TODO,
0334 (decided 2026-10-23: both ideas kept, in two TODOs). This TODO is the home page for a
**paired** phone, as decided on 2026-10-23 above.
