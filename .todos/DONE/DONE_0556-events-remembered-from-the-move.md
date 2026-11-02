# 0556 — An event remembers its photos: written by *Move to an event…*, not by hand

- **Priority**: Critical — the maintainer's top priority (2026-10-31): sort the photos left
- **Batch**: events
- **Depends**: —
- **Files**: `src/media_hygiene/search/move_go.py`, `src/media_hygiene/search/rule_models.py`, `src/media_hygiene/config/classify_rules.py`, `src/media_hygiene/classify/rules/calendar.py`, `src/media_hygiene/review/sort_rule.py`, `src/media_hygiene/places/` (tomlkit writer to share), the `people/` link code (0300), `src/media_hygiene/config/templates/config.toml.j2`

## Why

The maintainer never writes `date_range` rules by hand: they search a period (from… to…)
and press *Move to an event…* (`move_go.py`, 0403, which writes no rule today). A period
alone is the wrong definition of an event: on 1–3 April the maintainer is at one event,
a daughter at another. Mixing them is the failure to prevent.

## What

- An event = a name + its period + its **devices** (camera make/model of the files
  moved, serial number when EXIF has one, to check how often): three lines in
  `config.toml`, nothing more. Its files are those of its folder `YYYY/YYYY-MM/<name>`
  (the index knows them; the move is journaled): no list of files is stored.
- The files **refused** (in the window, not picked: never proposed again) go to
  `/config/events/<start date>-<name>.toml`, linked from `config.toml` as `/config/people/<name>.toml`
  (0300; decided with the maintainer, 2026-10-31: `config.toml` must not keep growing),
  by content id so they follow a move. Created only when there is a refusal.
- **An event is its name + its period, never its name alone** (the maintainer,
  2026-10-31: `Turin` every two or three years, one folder each time). Two events may
  share a name; the page shows them `Turin (July 2019)`, `Turin (April 2022)`. A move
  *to Turin* joins the `Turin` whose period touches the photos' days, else creates a new
  one (said in the dialog: "a new *Turin*, the one of 2019 is another"). Test: two
  `Turin` events, a move into each, a late photo of each.
- Everything the user defines lives under `/config`; `/cache` only what can be
  recomputed. Written by the page only (tomlkit, comments kept, atomic, as `places`
  does), read back and shown after the save. Never edited by hand.
- Files without a device in EXIF (received, scans, screenshots): no clue, **asked**.
- The event's folder renamed in Explorer: say how it is found again (by its files'
  content ids in the index, or asked); test it.
- *Move to an event…* saves the event on the same action (a line in the dialog says it
  will be remembered; no extra click). A move into an existing event adds to it.
- Existing `date_range` rules load as events with a period and no files: no migration.
- Two events sharing days are normal: drop "the first listed wins" (`sort_rule.py`
  overlaps) for events with devices; a file goes to the event whose devices it shares, and
  is **asked**, never guessed, when no device decides.
