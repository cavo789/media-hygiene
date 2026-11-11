# 0694 — The phone page served by the home server, so it gains ▶ Slideshow to the TV

- **Priority**: Medium
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/services/phone_review.py`, `src/media_hygiene/cli/cmd_phone_review.py`, `src/media_hygiene/services/launcher_phone_free.py`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/share/album_route.py`

Filed 2026-11-11 by the review of `feedback-2026-11-08-2-iterate.md` (0657, commit on
`iterate/2026-11-08`, pull request #75).

## Context

0657 gave the phone page (`phone-review`, *Free the phone*) the albums API (📚 Album ▾), but
not ▶ Slideshow to the TV: that page runs its own server, while the TV slot (the
`/screen` slideshow) lives in the home server. The reviews already run inside the home
server and get the slideshow, the way back home and *Apply now* from it.

## Decided (2026-11-11)

By the maintainer: **serve the phone page inside the home server**, like the reviews.
Left aside: keeping its own server and posting the slideshow to the home server over
HTTP (two servers to keep in step).

## Proposal

- Mount the phone page's routes in the home server (as the review pages are), its session
  kept the same (decisions saved at every choice, read back from the disk).
- `mh phone --free` / the launcher open it there instead of starting a server of its own;
  the typed command keeps working.
- ▶ Slideshow ▾ in its pick bar, as on the other tile pages (skill `photo-picking-pages`).

## Acceptance

- [ ] The phone page is answered by the home server; no second server is started
- [ ] ▶ Slideshow ▾ › On the TV starts the chosen tiles on `/screen` (test)
- [ ] The way back home and *Apply now* are there, as on every set-aside page
- [ ] Docs en + fr updated where they say how the page is opened; `docs_screenshots` to run

## Where the user gains

The phone page is the only tile page without the slideshow: after it, the same bar
everywhere (estimated from the pages listed by `photo-picking-pages`).

## Status — PARTIAL (2026-11-11)

### Done
- `/phone/` served by the home server (`services/phone_here.py`, `phone_here_parts.py`,
  listed in `pages_here`): `mh` (its watch loop, `$global:MediaHygieneKept`) writes the
  plan's lines in `.mh-phone-page.json` of the reports folder instead of starting a second
  container; the page writes `.mh-phone-ended.json` (the lines ticked, read back from the
  decisions file, on Delete; none on Leave), itself read back before answering; `mh` waits
  for it, or for the home server's end (nothing deleted then).
- The home page's tab opens the page itself: `GET /api/step` says `page: "/phone/"` while
  `mh` waits; `step_chip.html.j2` goes there once per step id (PC only).
- ▶ Slideshow ▾ (On this PC / On the TV) through the home server's `TvSlot`, ⌂ a plain link
  home, *Apply now* (pending = the decisions file's choices, `home_pending`); after Delete or
  Leave the tab goes back home, the step chip follows the deletion.
- The page's paths are relative (same page at `/` and under `/phone/`); the typed
  `mh import --phone --free` keeps its own server, unchanged (`phone_review`).
- Guests: `/phone/…` added to the route table of `test_lan_guests` (404); a phone of the
  family is refused too (`/phone/` is in no `lan_paths` list).
- Tests: `tests/unit/test_phone_here.py` (7); docs en + fr (`commands/import.md`).

### Not done
- A real try on the maintainer's PC with a phone (`mh`, *Make room on the phone* from the
  home page, Delete then Leave) — the PowerShell side (`_phone_kept`) is untested on Windows.
  **Reason:** needs Windows + a phone (maintainer).
- `docs_screenshots` to run (the bar gained ▶ Slideshow ▾). **Reason:** heavy, never run unasked.
- Headless browser check of the tab following to `/phone/` and back. **Reason:** time; the
  routes are covered by unit tests, the JS by review only.
