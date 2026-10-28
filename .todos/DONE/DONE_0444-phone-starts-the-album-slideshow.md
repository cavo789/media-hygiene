# 0444 — A paired phone starts the album slideshow on the TV (rest of 0369)

- **Priority**: High
- **Batch**: slideshow
- **Depends**: 0417
- **Files**: `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/home_parts.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/cli/menu_catalog_share.py`, `tests/integration/test_home_page.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Context

0369 (DONE) added the Share step *Show an album on the TV*, run from the PC only. Decided by
the maintainer (inbox of 2026-10-28): a paired phone may start **this one step** on the PC; every
other acting step keeps *Run this step on the PC*. The maintainer insists: this must be possible
(a required feature, not a nice-to-have).

## What to do

1. Whitelist the step `slideshow --album <name> --lan` for a paired phone (`lan_paths`,
   `POST /api/step`); an unpaired phone is refused.
2. A list of the saved albums (`albums.json`) instead of free text; no album saved → a message
   saying how to make one.
3. Once the slideshow is served from the home server (0417), the phone opens its remote.
4. Tests: PC, paired phone, unpaired phone refused, no album. Docs en + fr.

## Acceptance

- From the sofa, a paired phone starts the show of an album on the TV without touching the PC.

## Gain

Walk to the PC and type a command → two taps on the phone (estimated).

## Status

DONE (2026-10-28), in two steps.

1. Without 0417 (commit 9f18cff0): the phone's home page lists the albums of `albums.json`
   under *Show an album on the TV*; a tap sends `POST /api/step` for `slideshow-album`, let
   through by `review/lan_show.py` for that body and a saved album only (every other step
   still 403). Tests: `tests/unit/test_lan_show_album.py`.
2. With 0417 (the slideshow on the home server): an `mh` that keeps the home server up
   answers that step with the page `/slideshow/album/<name>` (`review/album_show.py`), the
   PC's form as well as the phone's tap: the show starts in the home server
   (`services/slideshow_here.py`), the remote opens at once, nothing stops. The TV's bookmark
   is `http://<addr>:8089/screen` (plain door): it waits while no show runs, is paired once by
   its code, and stays paired while the home server runs (the `Screens` live there); another
   album reaches it by itself. An older `mh` (no kept server) keeps step 1's way. Tests:
   `tests/unit/test_slideshow_here.py`.

The test on the real phone and TV is the maintainer's: item 11 of 0445.
