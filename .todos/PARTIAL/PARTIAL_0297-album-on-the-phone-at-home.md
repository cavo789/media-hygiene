# 0297 — An album on the phone at home: cover, mosaic by day, full screen

- **Priority**: Medium — the maintainer's scenario: a family member shows an album to visiting relatives, on their own phone, in the living room
- **Batch**: share
- **Depends**: 0295
- **Files**: `src/media_hygiene/share/album_page.py` (new), `src/media_hygiene/share/templates/album.html.j2` (new), `src/media_hygiene/share/templates/album.js.j2` (new), `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/slideshow/pictures.py`, `src/media_hygiene/slideshow/films.py`, `src/media_hygiene/cli/menu_catalog_share.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/`, `documentation/fr/commands/`, `tests/measure/mh-measure.ps1`

## Context

Designed in chat with the maintainer (2026-10-22): at home, someone builds an album (0295) and
shows it to relatives in the living room, without the TV, **on their own phone**. The phone is
paired once (`mh --lan`, its code or QR code, 0269); the relatives look at its screen and pair
nothing. Phones of other people (an album-only link, no pairing) are 0293's question, left
there.

## What to do

1. A page per album, for a phone held upright, on the model of the big photo apps:
   - **a cover**: the best photo full width (the sharpest of the first day, or chosen), the
     album's name, its dates and its place (offline, `geo/`);
   - **a mosaic** of thumbnails grouped by day ("Monday 10 July · Heraklion");
   - **a tap opens the photo full screen**, a swipe goes to the next or the previous one, a
     tap closes; the videos play in place as on the TV (0292: H.264 as it is, the others
     labelled).
2. Pictures sized for a phone (reuse 0291's resized JPEGs: `screen_jpeg`, a phone size to
   choose), the next ones preloaded; works on the home Wi-Fi only, while `mh` runs (said on
   the page and in the docs).
3. Reached from the *Share* area (0294) on the PC, and from the phone's home page once paired;
   the album list for a paired phone.
4. HTTPS is **not** part of it: the album reads fine over `http://`. Serving HTTPS too (a
   self-signed certificate kept under `/cache`, tied to the PC's address, a warning to accept
   on each phone) would only matter for the phone's share sheet (the Web Share API needs a
   secure context; whether a page past a certificate warning counts as one is **to check** on
   the maintainer's phone before any design). Left as a future idea, with that measurement
   first.
5. Docs en + fr, translations, `docs_screenshots` afterwards; `mh-measure.ps1`: a step with the
   maintainer's phone (scroll smoothness, time to open a photo, swipe, a video).

## Acceptance

- A paired phone lists the albums and opens one: cover, days, full screen, swipe (tests on the
  page's routes and on what a phone may see: only the albums, never the rest of the library
  unless already allowed by 0269).
- The maintainer's measure on the phone (the mh-measure step).

## Status — PARTIAL (2026-10-22)

### Done
- The albums' page, served in front of the home page (`share/album_page.py`, `share/album_shelf.py`, `services/album_pages.py`, `services/album_reader.py`, `share/templates/album.{html,js}.j2`): the list (cover, dates, place, count), an album (cover = sharpest photo of the first day, dates, offline place, mosaic by day named after its town), full screen with swipe, tap or Back to close, next pictures preloaded; videos in place as on the TV (H.264 as is, the others labelled).
- Phone-sized pictures: `screen_jpeg` with a square box of 1440 px (`ScreenJob.shape`), kept in `/cache`.
- Reached from the *Share* area (panel *Your albums*) and from a paired phone's home view; `review/lan_app.py` lets a paired phone reach the albums and **their** files only (thumbnails, pictures, videos; `/original/` and `/preview/` refused; a key of no album → 404), tested in `tests/integration/test_album_phone.py`.
- 0295 item 4: a paired phone takes a photo out of an album or adds it to another (`POST /api/albums`, `Origin` checked, keys limited to the albums' files), read back.
- Docs en + fr (`commands/home.md` § Your albums, on the phone; `share.md` Go further), French catalogue; `mh-measure.ps1` step 33.

### Not done
- The measure on the maintainer's phone (scroll smoothness, tap → full screen, swipe, a video, a change).
  **Reason:** needs the maintainer's phone and Wi-Fi: `.\mh-measure.ps1 -Only 33 -Count 120`.
- A cover chosen by the user (only the sharpest of the first day).
  **Reason:** needs a `cover` field in `albums.json` (schema change): asked in the feedback.
- `docs_screenshots` afterwards (home page and new albums page); HTTPS stays a future idea (item 4).
