# 0658 — TV slideshow: the very first title card also holds the timer back

- **Priority**: Low
- **Batch**: tv-slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/slideshow/slides.py`, `src/media_hygiene/slideshow/show.py`, `tests/unit/test_slideshow_story.py`

## Problem

Follows 0654 (commit c40d892b): an event's title card now pauses the show's timer, except the
very first one, when a TV joins a show not played yet (the show starts paused; play restarts
from the card end of the last move, which the first slide never had). Decided in the review of
2026-11-08: fix it, so the first photo keeps its full duration too.

## Fix

When play starts on a slide whose card was never timed (no move yet), count its card as for any
new event (`Timing.card_for`), then the interval.

## Acceptance

- [x] The first photo of a show just joined stays its full interval after its card (test, fake clock)
- [x] Pause/next during that first card behave as for the others (test)
