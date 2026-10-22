# 0291 — `slideshow`: show holiday photos on the TV, driven from the phone

- **Priority**: Low — an idea of the maintainer (2026-10-21), after 0269
- **Batch**: slideshow
- **Depends**: 0269
- **Files**: `src/media_hygiene/cli/cmd_slideshow.py`, `src/media_hygiene/slideshow/`, `src/media_hygiene/services/slideshow.py`, `src/media_hygiene/cli/menu_catalog_find.py`, `src/media_hygiene/config/`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`, `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `tests/measure/mh-measure.ps1`

## Context

The maintainer wants to show the photos of the last holidays on the living-room TV, the
family on the sofa, and pick the next photo from the phone, skipping some (2026-10-21).
0269 opens the pages to the home network (pairing code, token cookie, plain HTTP, LAN only,
read-only steps first): a slideshow is read-only (🔒), so it fits its first scope.

What `search/` already serves and this reuses: thumbnails (`/thumb/`), large previews
(`/preview/`), originals, the folder view, the search (dates, places, people), the files set
aside (`chosen`).

### Measured on the maintainer's devices (2026-10-21, by eye)

- TV: Samsung **UE55ES6100**, wired to the home network. The "E" series is 2012 and the panel
  Full HD (estimated from Samsung's naming, to check). Its "Internet" app is an old browser:
  plain HTTP only, a modern HTTPS site does not open.
- A test `nginx` container on the PC (`-p 8088:80`, so on every interface) was reached from the
  TV at `http://<PC LAN address>:8088/test.jpg`: network and firewall are fine.
- A 5 MB photo took ~2 s, painted in bands; the same photo resized to 1920 px (998 KB, saved by
  Windows Photos) ~1 s, still in bands. The wire is not the cost (5 MB at 100 Mbit/s ≈ 0.4 s,
  estimated): the TV's 2012 processor decoding is.
- The maintainer also has a Chromecast with a remote, so most likely a Chromecast with Google
  TV (to check in its *Settings → System → About*).

## Design (agreed in chat, 2026-10-21)

- **Two pages, one server on the PC**, no cast protocol:
  - **Screen** (`/screen`), opened in the Chromecast's browser (or the TV's): black, full screen, one photo, never a
    path or a file name. JavaScript a 2012 browser runs (ES3/ES5, `XMLHttpRequest`, no
    `fetch`, no modules). It long-polls the server ("what do I show?"), **loads the next photo
    in a hidden `Image` and swaps only once decoded**: the bands are never seen, the previous
    photo stays until then.
  - **Remote** (`/remote`), on the phone (paired by 0269): the selection as thumbnails, a tap
    sends one to the TV, ◀ ▶, play/pause with an interval, "do not show" to skip one live.
- **The server holds the state** (selection, current photo, timer): a TV reload or a phone
  going to sleep loses nothing.
- **Selection**: a folder, a search result, or the files set aside.
- **Reverse pairing for the TV**: the TV shows a short code, the paired phone confirms it
  (typing a code with a TV remote is painful).
- **TV previews**: JPEG at the screen's size (`[slideshow] screen_px`, default 1920, quality
  ~85, kept in the cache folder), EXIF orientation applied. Estimated 300–500 KB each.
- **A stable address** so the TV's bookmark keeps working: a fixed port (`[slideshow] port`)
  and the PC's address reserved in the home router (documented, not done by the tool).
- **Settings**: `port`, `screen_px`, the default interval — all three a user with another TV
  may want to change.
- **Photos only** here; videos are 0292.

## The Chromecast: the recommended screen (measured 2026-10-21)

The maintainer installed a browser app on the Chromecast with Google TV and opened the `nginx`
test URL: the photo shows, **faster than on the TV** (by eye, not timed). The same browser
opens the maintainer's own blog (HTTPS, heavy JavaScript): it is a modern browser.

- The **Screen page targets the Chromecast's browser first**; the TV's own browser stays
  supported as a fallback (the page is small: keeping it ES5 costs little).
- The raw JPEG URL showed at its natural size, to scroll: expected for a bare image. The
  Screen page fits the photo to the screen (`100vw`/`100vh`, `object-fit: contain`, black
  borders) and asks for full screen; documented for both browsers.
- Casting the PC's Chrome/Edge tab stays the last resort. The Google Cast SDK (HTTPS,
  registered receiver) is out of scope.

## What to do

- The verb `slideshow` (🔒): its command, its page in both languages (where the Samsung
  "Internet" app is, typing the address once and bookmarking it, full screen, the router
  reservation, plan B), `COMMANDS_TOO`, `menu_catalog_find.py`, `nav` of mkdocs, `i18n_update`.
- `mh` publishes the slideshow's port on the LAN only when 0269's option is given.
- A `mh-measure.ps1` step: the time from a tap on the phone to the photo on the TV.

## Acceptance

- Unit/integration tests: state machine (next, previous, jump, skip, timer), TV preview size
  and orientation, Host/token checks inherited from 0269, the Screen page's JavaScript free of
  post-ES5 syntax (a test parses it).
- The maintainer's evening test through the Chromecast (then the UE55ES6100's own browser): "next" shows without bands and at once
  (preloaded), a jump to any thumbnail in ~1 s with no bands (target estimated from the
  measures above). An unattended run closes PARTIAL on it.

## Status — DONE (2026-10-22)

### Done
- `media-hygiene slideshow` (🔒, a page command): `--folder` (and its subfolders), `--search`
  (the words of `search`) or `--chosen` (the files set aside), exactly one; photos only (images
  and RAW), oldest first, the undated last, at most 3,000 (`services/slideshow_pick.py`).
- One server, two pages (`slideshow/`): the **screen** `/screen` (ES5 only, XMLHttpRequest long
  poll `/api/wait/<version>`, two stacked layers: the next photo loads and decodes behind the one
  shown, swapped once decoded, `img.decode()` where it exists; the following one preloaded;
  never a name or a path; OK/click asks for full screen; letterboxed without `object-fit`) and
  the **remote** `/` (thumbnails, ◀ ▶, play/pause, the interval, "Do not show" / "Show again", a
  tap jumps; the PC's page shows the TV's address, the phone's address, code and QR code).
- The server holds the show (`show.py`, `desk.py`): next/previous go round passing over the
  photos set out, a jump sets a photo back in, the timer is read by whoever waits (no task).
- Access (`door.py`), reusing 0269 (`LanAccess`, `Pairing`, `pair_page`, `lan_response`): the
  loopback does everything; under `mh --lan` the exact `Host` of the PC's private address only;
  a phone paired by the run's code drives the show; a **TV paired the other way round**
  (`screens.py`: a token in an HttpOnly cookie, a 6-digit code shown on the TV, typed on the
  paired phone; 8 TVs waiting at most, 5 wrong codes close it); a stranger gets the pairing
  pages only; only the show's photos are served (`/tv/<key>.jpg`, `/thumb/<key>.jpg`), never an
  original. The phone's `Origin` checked (another site's POST refused).
- TV pictures (`screen_jpeg.py`): EXIF orientation applied, fitted into `screen_px` × 9/16,
  quality 85, baseline, kept in the cache folder (trimmed with the previews).
- `[slideshow] screen_px` (1920) and `interval_seconds` (8) in `config.toml`; the port is
  `[review] port` (see the feedback's question).
- `mh slideshow … --lan` (PowerShell): the address and secret of 0269 (`_mh_lan_open`, split out
  of `_mh_lan`), the slideshow's port published on the PC's private address too; the home page
  of `mh --lan` publishes it for the slideshow step too; the bash `mh` refuses `--lan` anywhere.
- The catalog step *Show your photos on the TV* (find stage, *Go further*, a folder field), the
  command's page in both languages (Chromecast first, the TV's Internet app, the bookmark, the
  router reservation, plan B: casting a tab), `reference-commands`, `launcher`, `home`, mkdocs
  nav, `COMMANDS_TOO`, translations, the CLI help capture.
- Tests: `test_slideshow_show.py` (state machine, timer, long poll), `test_slideshow_screen.py`
  (the screen script parsed for post-ES5 syntax, TV picture size/orientation/cache),
  `test_slideshow_app.py` (Host, phone and TV pairing, Origin, only the show's photos),
  `test_slideshow_pick.py`, `test_slideshow_command.py`, `test_home_lan.py` (both `mh`).
- Step 30 of `tests/measure/mh-measure.ps1`: the evening test, timed by hand.

### Measured on the maintainer's TV (2026-10-22, `mh-measure.ps1 -Only 30 -Count 30`)
- Chromecast's browser: "next" (preloaded) median 0.5 s (the very first 10.1 s, cold), a jump
  to a far thumbnail median 0.5 s, never bands; full screen, the timer, "do not show", the TV
  reloaded and the phone asleep all right. The UE55ES6100's own Internet app: next and jump
  median 0.5 s, no bands.
- First run: the Chromecast showed the lines but not the 6-digit code (a fixed 120 px under
  its text zoom), and parts of the former photo stayed on the new one. Fixed: the code sized
  in vh then shrunk by the script until it fits, the layer behind hidden where `img.decode`
  exists, and the TV names the phone's address (asked by the maintainer). Second run, photos
  of one holiday folder: code whole, address shown, no trace of the former photo.

### Was not done (closed by the measure above)
- The evening test on the living-room TV through the Chromecast's browser, then the
  UE55ES6100's own browser: "next" without bands and at once, a jump in ~1 s without bands, the
  TV's code readable, full screen, the TV reloaded, the phone asleep.
  **Reason:** needs the maintainer's TV, Chromecast and phone: `mh-measure.ps1 -Only 30 -Count 30`
  (image built from branch `iterate/2026-10-21-2`).
