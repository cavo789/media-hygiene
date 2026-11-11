# 0660 — One ▶ *Slideshow* ▾ menu in the pick bar: on this PC or on the TV

- **Priority**: Medium
- **Batch**: tv-slideshow
- **Depends**: 0659
- **Files**: `src/media_hygiene/review/templates/pick_acting.html.j2`, `src/media_hygiene/review/templates/album_bar.html.j2`, `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/review/templates/pick_bar.css.j2`, the home page's slideshow choice

## Problem

📺 *On the TV* sits in the pick bar of search, browse and the burst review (0454, 0655) and is
**hidden** when no TV is paired; 0659 adds a second target, this PC. Two buttons would widen bars
already on two lines, and the hidden 📺 makes the slideshow invisible without a TV.

## Decided (2026-11-08, maintainer, after discussing it)

One menu, the same component as 📚 *Album* ▾ (`<details class="barPanel">`):

- ▶ **Slideshow ▾**, always shown on these pages, at the place of 📺 today.
- Entries: 🖥 **On this PC** (0659) · 📺 **On the TV** — greyed when no TV is paired, with one
  line *No TV paired: how* linking to the slideshow chapter.
- The target used last comes first (per viewer, localStorage, wrapped in try/catch); no shortcut
  that starts without showing the menu.
- Same rule as 📺 today: the files picked, or nothing picked → the page's files (the count said
  in the entry: "On this PC · 120 photos").
- The home page's slideshow choice offers the same two targets.
- Off the PC (a paired phone) the menu is not shown: the phone keeps its big *Show on the TV*
  buttons.

## Acceptance

- [x] One ▶ *Slideshow* ▾ in the bar of search, browse, burst review; no 📺 button left (tests)
- [x] *On the TV* greyed with its *how* line when nothing is paired; works when paired
- [x] *On this PC* starts the show and opens the full-screen tab (0659)
- [x] Bar width not grown: grid top unchanged at 1280 and 1920 px (headless Chromium, skill `photo-picking-pages`)
- [x] Docs en/fr (slideshow, search, browse, review); `docs_screenshots` flagged stale

## Done (2026-11-08)

- `slideshow_menu.html.j2` (the `.barPanel` of 📚 Album ▾) + `pick_slideshow.js.j2`, in
  `pick_acting.html.j2` where 📺 was (`tv_here`); `tvSend` removed. Count said at each opening
  (picked, or every file of the page), 📺 greyed + *No TV paired: how* (`header.slideshow`, the
  slideshow chapter) until `/api/tv-paired` says yes; last target first (localStorage
  `mh-slideshow-target`, try/catch); hidden off the loopback (a paired phone).
- Line 1 at 1280 px: the word *Slideshow* made the lead wrap (+9 px grid top, measured); below
  1600 px the summary shows ▶ ▾ only (its title and aria-label keep the word). Grid top then
  276 px with and without the menu at 1280 and 1920 (headless Chromium, burst review, API mocked).
- Home page: the forms of *Show your photos on the TV* and *Show an album on the TV* have two
  buttons, 🖥 On this PC and 📺 On the TV (last used first, same key); `?here=1` on
  `/slideshow/album/…` and `/folder/…` leads to the screen (`started_at`). The form now follows
  `reply.body.page` (it used to open the run dialog on an in-server show).
- The PC's "show is over" screen: its own wording (`screen_here.html.j2` `data-over`).
- `docs_screenshots` should run (bars of search, browse, burst review changed).
