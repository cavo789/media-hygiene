# 0832 — Slideshow remote: tiles grouped by event, a checkbox per event

- **Priority**: High
- **Batch**: tv-slideshow
- **Depends**: none (0831 adds the "Will not be shown" group: do them together if both open)
- **Files**: `src/media_hygiene/slideshow/templates/slideshow.html.j2`, `src/media_hygiene/slideshow/templates/slideshow.js.j2`, `src/media_hygiene/slideshow/pictures.py`, `src/media_hygiene/slideshow/desk.py`, `src/media_hygiene/slideshow/show.py`, `src/media_hygiene/slideshow/chapters.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Reported (maintainer, 2026-11-15)

1. Under the *event's name* buttons, the remote shows a lone title ("Catane (Sicile) · avril
   2026") for a show of all 2026: it is the event of the photo shown now (0448), but
   nothing says so — "pas du tout explicite", read as the name of the selection.
2. Wanted instead: the grid **grouped by event** (the chapters 0448 already cuts:
   `2026/2026-01/Nouvel An`, `2026-04/Pâques`, `2026-07/Vacances`…), each group with its
   heading, its count and a **checkbox, ticked by default**: unticking
   `2026-09/Rentrée des classes` sets all its photos out of the show; ticking brings them
   back. Choose a whole year, then remove events.

## What

- Groups = the slideshow's **chapters** (`slideshow/chapters.py`, 0448), already on every
  slide: a run of photos of the **same folder**, named after its deepest meaningful folder
  (`2026/2026-04/Pâques` → *Pâques*), the same that names the TV's title card. **Not** the
  🗂 Events tab of `/library`: those are the classify plan's events or time-gap events of
  unsorted files (`search/events_desk.py`, `span_events.py`), another cut. A slide with no
  chapter in an *Other photos* group. Heading: the event's name · month · count. The
  folder is the key: two runs of the same folder (show order interleaved) are one group.
- Checkbox per group → `POST /api/show` with a new action (or `/api/avoid`'s way): set out /
  back in every key of the event; a photo set out by hand stays out when the event is
  ticked again (same rule as *Avoid some people*). Counts updated by the long poll.
- The **current photo's event**: no lone line under the buttons any more; the group being
  shown is marked (as the current tile is), and the status line says
  "Photo 17 of 344 · Catane (Sicile) · april 2026".
- Shared parts: load `photo-picking-pages`; reuse the **look** of an existing grouped tile
  grid (headings, group checkbox — find it among `/people` sections, `/library`'s groups)
  rather than a slideshow-only copy; the data stays the chapters. Also the size switch of tiles (see 0830).
- With 0831, the "Will not be shown" group comes last, holding the events unticked too
  (reason: the event's name).

## Tests

- A show over two events: two groups, in order, with their counts.
- Unticking an event sets out its photos only; ticking brings them back, but a photo set
  out by hand stays out.
- The status line names the current event; the lone line is gone.
