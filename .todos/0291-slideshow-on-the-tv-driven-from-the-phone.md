# 0291 — `slideshow`: show holiday photos on the TV, driven from the phone

- **Priority**: Low — an idea of the maintainer (2026-10-21), after 0269
- **Batch**: slideshow
- **Depends**: 0269
- **Files**: `src/media_hygiene/cli/cmd_slideshow.py`, `src/media_hygiene/slideshow/`, `src/media_hygiene/services/slideshow.py`, `src/media_hygiene/cli/menu_catalog_find.py`, `src/media_hygiene/config/`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`, `tests/support/docs/scenario.py`, `.config/mkdocs/mkdocs.yml`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: the evening test on the living-room TV, through the Chromecast's browser (and the TV's own as fallback)

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
