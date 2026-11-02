# 0558 — Photos arriving later in an event's days: proposed on the grid, refusable

- **Priority**: Critical — the maintainer's top priority (2026-10-31)
- **Batch**: events
- **Depends**: 0556, 0557
- **Files**: `src/media_hygiene/search/events_desk.py`, `src/media_hygiene/search/events_choose.py`, `src/media_hygiene/review/templates/pick_*` (load skill `photo-picking-pages`)

## Why

The one real gain of a remembered event over a search by period: photos of the same
days arriving later (a spouse's phone, a USB stick found, a friend's photos).
Nothing moves blindly (memory "Seeing first").

## What

- Files of the index inside an event's window, neither in its folder nor refused, are listed
  "12 new photos during *Easter at grandma's* — see them?" on the events page and home.
- On the shared pick grid, ranked by device: same camera → ticked
  ("probably"); another camera → unticked ("during, but elsewhere"); matching
  **another** event of the same days better → proposed there instead. No device in EXIF → asked.
- *Add* moves them (`move_go`, journaled) and adds them to the event; *Refuse* records
  them in `/config/events/<start date>-<name>.toml` (never proposed again); both read back and shown.
- *Apply now* standard and the way back home, as every set-aside page.
