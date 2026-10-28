# 0448 — slideshow: the TV tells the event (name, month, place), a title card per event

- **Priority**: High
- **Batch**: slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/slideshow/slides.py`, `src/media_hygiene/slideshow/show.py`, `src/media_hygiene/slideshow/screen_api.py`, `src/media_hygiene/slideshow/templates/screen.html.j2`, `src/media_hygiene/slideshow/templates/screen.js.j2`, `src/media_hygiene/slideshow/templates/slideshow.html.j2`, `src/media_hygiene/slideshow/templates/slideshow.js.j2`, `src/media_hygiene/services/slideshow.py`, `src/media_hygiene/geo/` (gazetteer, areas), `src/media_hygiene/classify/` (event names, places), `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Why

The maintainer, 2026-10-28: the person who shows the photos to the family on the TV needs help
to tell them: which event, when, where. Validated design (all points, maintainer):

## What

1. **The event's name from its folder**: `2026/2026-10/Promenade à Valkenburg` → *Promenade à
   Valkenburg*: the deepest folder that is not a year (`2026`), a year-month (`2026-10`), a
   date or a generic name (reuse the "generic folder" notion of `plan/KeepPolicy` /
   `classify` if one exists). No such folder: no name.
2. **The period**: the month and year of the event's photos (EXIF date taken, `media_day`),
   localized (*octobre 2026* / *October 2026*); a span across months says both
   (*juillet – août 2023*).
3. **The place**: first an area the user named in `mh places` (`[[classify.places]]`, circle
   or OSM area, `classify/whereabouts.py`, `place_match.py`); else the nearest town of the
   photos' GPS (offline gazetteer, `geo/`); else nothing. Never a request to the internet.
4. **A title card on the TV at each new event**, like a chapter: one of its photos blurred as
   the background, the name large, the period and the place under it, ~3 s (a named
   constant), then the photos. Also a small **banner** (name · period · place) for a few
   seconds on the first photo of the event, never permanently.
5. **Shown where, chosen from the phone in one tap** (the remote): *TV and phone*, *phone
   only*, *nowhere*. Default: the title card on the TV, the details on the phone. The choice
   is kept for the show (the server's state), the TV follows it at once.
6. An event = consecutive photos of the same folder in the show's order (an album may mix
   folders: each change of folder is a new event).

## Tests

Name from folders (year, year-month, dates, generic, accents kept), period (one month, a span,
no date), place (a named area wins over the town, GPS missing), the title card served once per
event, the phone's choice reaches the TV's state. Docs en+fr; `docs_screenshots` to run.

## Explicit NON-goals

- The storyteller's view on the phone (0449).
- Editing event names (the folder is the name).

## Status — PARTIAL (2026-10-28)

### Done
- Name from the folder (years, months, dates, device folders and the drive's top folder passed),
  period (one month, a span, across years), place (user's place, else nearest offline town).
- Title card on the TV at each new event (blurred photo, name, period, place, 3 s), then a banner
  5 s; three buttons on the phone (TV and phone / Phone only / Nowhere), kept in the server's state.
- Tests `tests/unit/test_slideshow_story.py`; docs en+fr (`commands/slideshow.md`).

### Not done
- Documentation captures not regenerated.
  **Reason:** `docs_screenshots` is heavy, run it unasked never: the maintainer runs it.
- Checked on a real TV/Chromecast (card timing, blur on the 2012 TV's browser).
  **Reason:** needs the maintainer's TV.
- The title card does not pause the show's timer (it eats up to 3 s of the first photo).
  **Reason:** kept simple for a first TV test; decide after seeing it.
