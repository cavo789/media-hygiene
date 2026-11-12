# 0614 — The TV's address `http://<PC>:8089/` opens a welcome page, not the phone's steps

- **Priority**: Medium
- **Batch**: phone
- **Depends**: 0461 (PARTIAL, *On this day*)
- **Files**: `src/media_hygiene/services/slideshow_here.py`, `src/media_hygiene/slideshow/tv_door.py`, `src/media_hygiene/slideshow/templates/`, `documentation/en/`, `documentation/fr/`

## Why (maintainer, 2026-11-05)

To start a slideshow the maintainer types `<IP>:8089/screen` on the TV. Served by the home
server, the plain door's `/` redirects to the **phone's** install steps
(`slideshow_here.py`, `TV_HOME` → `PHONE_STEPS`); served by `mh slideshow`, it redirects to
`/screen`. The TV should land on a page of its own at the bare address. The Gemini lead of
0293 (closed) stays the spirit: a welcome page, but every fact true and offline.

## What

- `/` on the plain door: a welcome page, two large tiles driven by a TV remote (arrows + OK,
  focus visible from 3 m): **📺 This is the TV** → `/screen` (pairing code), **📱 Install on my
  phone** → the current steps page.
- `[home] family_title` as title; one line of index facts (photos, years covered); once 0461
  builds it, an *On this day* photo as background.
- A TV already paired (screen cookie) under `mh slideshow` keeps going straight to `/screen`.
- No CDN, no endless animation, no clock (0293's rules); CSP unchanged; i18n en + fr.

## Acceptance

`http://<PC>:8089/` on a TV shows the page in both servers; OK on the first tile opens
`/screen`; a paired TV skips it; tests per server; docs en + fr (the TV address now without
`/screen`); `docs_screenshots` to run.

## Status — PARTIAL (2026-11-05)

### Done
- `/` on the plain door (8089) shows a welcome page in both servers (home server and `mh slideshow`): meerkat (app icon, `/app-icon-192.png`), `[home] family_title` (fallback "Our photos"), two remote-driven tiles (📺 → `/screen`, 📱 → `/phone`); a paired TV still goes straight to `/screen`. Commit c02b34d9; tests for both servers; docs en + fr; i18n.

### Not done
- The line of index facts (photos, years covered).
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  **Reason:** needs a new index query; left out to keep the change small.
- The *On this day* background.
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  **Reason:** waits for 0461.
- Arrow keys and focus not tried on a real TV browser; `docs_screenshots` to run.
