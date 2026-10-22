# 0294 — A *Share* area on the home page, outside the cycle: the slideshow first

- **Priority**: Medium — asked by the maintainer (2026-10-22): the slideshow sits in *Find*, where nobody would look for it
- **Batch**: share
- **Depends**: —
- **Files**: `src/media_hygiene/cli/menu_entry.py`, `src/media_hygiene/cli/menu_catalog_find.py`, `src/media_hygiene/cli/menu_catalog.py`, `src/media_hygiene/cli/menu_catalog_share.py` (new), `src/media_hygiene/cli/home_tiles.py`, `src/media_hygiene/cli/home_cycle.py`, `src/media_hygiene/search/templates/browse.html.j2`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`, `tests/unit/test_menu_catalog.py`

## Context

0291 put `slideshow` (*Show your photos on the TV*) in the *Find* stage, group *Go further*
(`menu_catalog_find.py`). The maintainer challenged it (2026-10-22): *Find* answers "where is
this photo?"; showing the holidays to the family is a goal of its own, the reason the library
is kept tidy, not a stage of keeping it so. A user who wants the photos on the TV does not open
*Find*.

## Decided (2026-10-22, by the maintainer, in chat)

- A **Share** area (*Partager* in French), **outside the five-stage cycle** (Import → Clean →
  Sort → Find → Back up), shown apart on the home page like History, Reports and Settings, but
  visible (it is a goal, not a tool).
- Its name is *Share*, not *Project* nor *Enjoy*: it will later hold the other ways to share —
  the TV (now), the phone (0293, the family landing page), maybe an album made for social
  networks.
- `slideshow` moves there (out of *Find*); first and only step for now.

## What to do

1. A `Space.SHARE` area (`menu_entry.py`), its own catalog module, no `stage=` number (outside
   the cycle); the home page shows it apart from the cycle, with its icon and one line (e.g.
   "Your photos on the TV, the phone as the remote").
2. `slideshow` leaves `menu_catalog_find.py`; its keywords keep "tv television chromecast"
   (the home page's search still finds it).
3. Proposed in chat, to confirm with the maintainer before code (left out if not): a
   **Share on the TV** button in the search and browse pages, starting `slideshow --search` /
   `--chosen` on what was found or chosen — where the user stands after finding.
4. Docs en + fr: `commands/home.md` (the areas), `commands/slideshow.md` (where to start it);
   translations; `docs_screenshots` to run afterwards (the home page changes).

## Acceptance

- The home page shows *Share* apart from the cycle, with the slideshow in it; *Find* no longer
  lists it; `mh menu` lists it under *Share*.
- `tests/unit/test_menu_catalog.py`: every step in exactly one area; *Share* has no stage
  number.
- Docs both languages, French catalogue complete.

## Decided (2026-10-22, by the maintainer, `/todo:iterate`)

Item 3: the *Share on the TV* button in search and browse comes with the albums (0295), and
shows the current album; this TODO makes the *Share* area only.
