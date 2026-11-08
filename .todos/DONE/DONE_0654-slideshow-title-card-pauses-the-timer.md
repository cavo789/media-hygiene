# 0654 — TV slideshow: the event's title card pauses the show's timer

- **Priority**: Low
- **Batch**: tv-slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/slideshow/templates/`, `tests/unit/test_slideshow_story.py`

## Problem

Follows 0448 (PARTIAL). At each new event the TV shows a title card for 3 s (blurred photo, name,
period, place), but the show's timer keeps running: the event's first photo loses up to 3 s of its
duration. Decided by the maintainer in the inbox of 2026-11-08: pause the timer while the card shows.

## Fix

Start the photo's countdown when the card hides, not when the slide begins. A paused show (phone
remote) stays paused through the card; *next* on the remote skips the card.

## Acceptance

- [ ] The first photo of an event stays on screen its full duration after the card
- [ ] Pause and next from the remote behave the same during the card (test)
- [ ] Docs en/fr `commands/slideshow.md` if they state the timing
