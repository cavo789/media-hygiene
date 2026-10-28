# 0449 — slideshow: the storyteller's view on the phone, and story controls

- **Priority**: Medium
- **Batch**: slideshow
- **Depends**: 0448
- **Files**: `src/media_hygiene/slideshow/templates/slideshow.html.j2`, `src/media_hygiene/slideshow/templates/slideshow.js.j2`, `src/media_hygiene/slideshow/desk.py`, `src/media_hygiene/slideshow/show.py`, `src/media_hygiene/slideshow/app.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Why

Validated by the maintainer (2026-10-28): the person telling the story reads notes on the phone
while the family looks at the TV.

## What

- **The storyteller's view** on the phone's remote: the photo shown now (larger), its event
  (0448), date **and time**, place, the people recognised (`people`, if any), its description
  and words (`tags`, if any), and the next photo. Read-only (memory `phone-read-only`).
- **Story controls**: *pause while I talk* (one tap, the show waits), *back to the start of
  this event*, *next event*.
- **A small map of the event** (its photos' positions, from the index's GPS) in the
  storyteller's view, offline: the vendored Leaflet of `places/` without tiles, or a simple
  drawing of the points over the event's towns (to decide at implementation: no tile request
  unless `[places] tiles` is set, as in `places`).

## Explicit NON-goals

- Anything that changes photos, albums or the index from the phone.

## Status — PARTIAL (2026-10-28)

### Done
- The storyteller's notes on the remote (a fold under the controls): the photo shown larger (its
  thumbnail), day and time, event and place, description (`caption`, else Takeout) and the vision
  words (`tags`), the next photo; read from the index only (`services/slideshow_notes.py`).
- Story controls: *Pause while I talk*, *Back to the start of this event*, *Next event*
  (actions `event`, `next_event`; past the last event the show stays). No write route.
- The event's map: an SVG drawing of its photos' positions (this one in red), over the labels of a
  handful of nearby towns from the offline gazetteer (`slideshow/event_map.py`); when the user set
  `[places] tiles`, over those tiles instead, the remote's CSP allowing that host only
  (`services/slideshow_map.py`).
- Tests `tests/unit/test_slideshow_notes.py`; docs en+fr (`commands/slideshow.md`).

### Not done
- The people recognised.
  **Reason:** their names are made at each search from the face lists (never in the index);
  reading them at show start needs the faces machinery — a follow-up.
- Checked on a real phone; documentation captures not regenerated (`docs_screenshots`).
  **Reason:** needs the maintainer's phone; captures are run by the maintainer.
