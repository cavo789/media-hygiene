# 0831 — Slideshow remote: the photos set out in their own group, "Will not be shown"

- **Priority**: Medium
- **Batch**: tv-slideshow
- **Depends**: none
- **Files**: `src/media_hygiene/slideshow/templates/slideshow.html.j2`, `src/media_hygiene/slideshow/templates/slideshow.js.j2`, `src/media_hygiene/slideshow/avoid_desk.py`, `src/media_hygiene/slideshow/desk.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Reported (maintainer, 2026-11-15)

On `/slideshow`, ticking a person in *Avoid some people* (0825) greys their photos in
place, among the others: in a show of 344 photos they are hard to find. Wanted: the
grid in two groups — first the photos that will be shown, then a group **"Will not be
shown"** holding every photo set out, those of André and of every other person ticked
(and those set out by hand with *Do not show*).

## What

- Two sections in the grid, each with its count: *Will be shown (n)*, then *Will not be
  shown (n)*; a photo moves from one to the other at once (the long poll already sends
  `out`).
- Each tile of the second group says why: the person(s) ticked whose photo it is
  (`✓ André` / `≈ André`), or *by hand*. Needs `GET /api/avoid` to give, per key, the
  names (`AvoidDesk` knows `Seen` per person).
- *Show it again* on a tile of the second group (`Action.IN`): it comes back, even if
  its person stays ticked (a choice by hand wins; `AvoidDesk.set_out` forgets it).
- Shared parts: the group headings as on other grouped tile pages (load
  `photo-picking-pages`; find the existing grouped grid, e.g. `/library`'s events or
  `/people` sections, and reuse it — no slideshow-only copy).
- With 0830 (large view) the tiles of both groups open the same large view.

## Tests

- Ticking a person moves their photos to the second group with the reason; unticking
  brings them back to the first, in the show's order.
- *Show it again* on one: back in the first group, stays there while the person is ticked.
- A photo set out by hand shows *by hand*.
