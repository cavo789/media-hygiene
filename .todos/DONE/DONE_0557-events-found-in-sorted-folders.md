# 0557 — Find the events already sorted in YYYY/YYYY-MM/<name> and fill the list

- **Priority**: Critical — the maintainer's top priority (2026-10-31)
- **Batch**: events
- **Depends**: 0556
- **Files**: `src/media_hygiene/classify/own_events.py`, `src/media_hygiene/search/events_desk.py`, `src/media_hygiene/search/rule_models.py`, `src/media_hygiene/index/` (read only)

## Why

The maintainer has already sorted dozens of events by hand into `YYYY/YYYY-MM/<name>`
(their words, 2026-10-31). Without them the event list is empty and 0558 has nothing to
propose late photos to.

## What

- Walk the index (no new disk walk) for folders shaped `YYYY/YYYY-MM/<name>` (and the
  shapes `own_events.py` already recognises: a meaningful name, not a date, a device or
  a person's), read each one's files: period = first → last dated photo/video,
  its devices (0556). No file list is stored.
- Show them on the events page as a **ticked list** ("38 events found in your folders"),
  each with its period, count and a few thumbnails; the user **unticks** the folders
  that are not events worth remembering (the maintainer's examples, 2026-10-31:
  `Restaurant`, `Concours de grimace des filles`), then confirms; only the ticked ones
  are written to `config.toml` (0556's writer). Untick all / tick all, and a filter by
  name, since there are dozens.
- An unticked folder is **remembered** as not an event (a user's choice: under
  `/config`, next to the refusals of 0556, by folder followed as 0556 does): the next
  scan never proposes it again; it can be ticked back from the same list (a "not
  events" section, folded).
- Folders of the same name in different years (`2019/2019-07/Turin`,
  `2022/2022-04/Turin`) are **separate events**, each with its own period (0556:
  name + period).
- A folder with a gap longer than `merge_gap_hours` (a batch, `Prints jan10`) is not one
  event: shown apart, not proposed.
- Already-known folders (an event with the same folder) are not proposed twice; a
  re-run after new sorting proposes only the new folders.
- Tests: the demo tree with two events sharing days in two folders; a folder renamed in
  Explorer after acceptance (the event is found again, 0556).
