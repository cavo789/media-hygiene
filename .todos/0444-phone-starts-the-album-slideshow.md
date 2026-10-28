# 0444 — A paired phone starts the album slideshow on the TV (rest of 0369)

- **Priority**: Low
- **Batch**: slideshow
- **Depends**: 0417
- **Files**: `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/home_parts.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/cli/menu_catalog_share.py`, `tests/integration/test_home_page.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Context

0369 (DONE) added the Share step *Show an album on the TV*, run from the PC only. Decided by
the maintainer (inbox of 2026-10-28): a paired phone may start **this one step** on the PC; every
other acting step keeps *Run this step on the PC*.

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
