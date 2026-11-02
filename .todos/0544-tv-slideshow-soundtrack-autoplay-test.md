# 0544 — TV slideshow soundtrack: test whether the TV plays sound without a click

- **Priority**: Low
- **Batch**: tv-slideshow
- **Depends**: 0508
- **Files**: `src/media_hygiene/review/templates/` (a test page), `src/media_hygiene/review/shared_routes.py`, `tests/unit/` (route test)
- **Needs maintainer**: the test on the family TV

## Reported (maintainer, 2026-10-31)

During a family meal a playlist (Spotify-like) often plays; wanted: a soundtrack for the random
slideshow of 0508 — soft jazz, for instance.

## Proposed design (not to implement yet)

- No music in the image (licences, size, taste): the user's own folder of tracks
  (mp3/m4a/ogg), mounted read-only like the photos, never under `/config`.
- The TV page plays them with an `<audio>` element: shuffled, cross-fade, stops with the show.
- The phone: a "🎵 Music" choice next to "🎲 At random", then pause / next / volume
  (read-only page: nothing written).
- Free sources the user may download (licences to check before naming them in the docs):
  Incompetech (CC BY), Free Music Archive, Jamendo, Pixabay Music (no redistribution).
  Maintainer's listening (2026-10-31): all fine but Musopen (overrun by ads): do not name it.

## Second question: local files or a remote playlist?

Maintainer (2026-10-31): must the music be downloaded, or can the TV play a remote link? To test.

- **Local folder**: works offline, no request leaves the house, but the user downloads first.
- **Remote URL**: an `<audio>` element plays a direct audio file URL (`.mp3`) if the page's CSP
  allows that host (`media-src`) — a playlist *page* (Spotify, a Jamendo web page) is not an
  audio file and cannot be played this way; a site with an API giving stream URLs (Jamendo has
  one, key required — to check) could. Cost: the TV contacts that host (its IP, what is
  played), needs the Internet; to state on the page, opt-in like `[places] tiles`.

## Blocking question: autoplay

Browsers refuse to start sound without a user gesture on the page. The show is started from the
phone, not from the TV: whether the TV page may play sound then depends on the device showing it
(TV browser, Chromecast, PC on HDMI) — unknown, to measure first.

## This TODO: the test only

1. A minimal test page (served like the TV page) that, once opened on the TV, starts a short
   generated tone (Web Audio, no file shipped) and an `<audio>` element when the phone sends
   the order, and shows on screen what happened (`play()` resolved / `NotAllowedError`).
   A second button plays a **remote** URL the maintainer pastes on the phone (a direct `.mp3`
   link of Pixabay or Incompetech), the test page's CSP allowing that host only.
2. The maintainer opens it on the TV the way the slideshow is shown, taps "Play" on the phone,
   and reports: sound with no click on the TV? after one click on the TV? never? And does the remote link play?
3. Result in this file → then decide: implement the soundtrack (a follow-up TODO with the design
   above), a "click once on the TV" hint, or drop it (Spotify beside the show already works).

## Gain (estimated)

One gesture instead of two (show + separate music app), music ending with the show; small gain,
hence the test before any implementation.
