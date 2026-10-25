# 0369 — Slideshow of an album started from the home page, by the PC or a paired phone

- **Priority**: Low
- **Batch**: slideshow
- **Depends**: 0357, 0360
- **Files**: `src/media_hygiene/cli/menu_catalog_share.py`, `src/media_hygiene/review/home_parts.py`, `src/media_hygiene/review/templates/home_run.js.j2`, `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/services/slideshow.py`, `tests/integration/test_home_page.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Context

Review of the feedbacks of 2026-10-21 (0291) and 2026-10-22 (0295), maintainer 2026-10-25: a
paired phone may start the slideshow itself (it is 🔒, it asks nothing in PowerShell; today a
phone runs only the audit, 0269's decision 3), and the Share area gets a step *Show an album on
the TV*. Today: `mh slideshow --album <name> --lan` typed in the console.

## What to do

1. Share area: *Show an album on the TV* — a list of the saved albums (`albums.json`), then the
   step `slideshow --album <name> --lan` through the channel of 0355 (the home server stays up).
2. The same step allowed from a paired phone (0360's list of what a phone may do): read-only,
   like the audit; the other steps keep *Run this step on the PC*.
3. Once 0357 serves the slideshow from the home server, the step opens its remote on the phone.
4. Tests: the step from the PC and from a paired phone; an unpaired phone refused; no album
   saved → the step says how to make one. Docs en + fr.

## Acceptance

- From the sofa, the phone paired on the home page starts the show of an album on the TV,
  without touching the PC.

## Gain

Starting a show: walk to the PC and type a command → two taps on the phone (estimated).
