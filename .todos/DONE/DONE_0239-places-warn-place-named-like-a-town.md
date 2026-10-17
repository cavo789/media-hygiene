# 0239 — `places`: a place named like a town says it may be redundant

- **Priority**: Low
- **Batch**: places
- **Depends**: —
- **Files**: `src/media_hygiene/places/board.py`, `src/media_hygiene/places/templates/places.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_places_command.py`, `documentation/en/commands/places.md`, `documentation/fr/commands/places.md`

## Seen

Maintainer, 2026-10-17: had saved towns as places ("Blankenberge", "Durbuy", …), then found
"Blankenberge" a second time in "Folders named after a town" and asked whether it was one place
or two. Explained in the chat: `classify` already names the towns from GeoNames; "Your places"
is for the spots GeoNames does not know (home, the grandparents', the office) or that should be
named otherwise. The maintainer: "I made a mistake, I will delete my places that are towns." The
page let the mistake happen without a word.

A town as a place is not always wrong: an OSM area gives exact borders (the nearest-town
guess may name a photo after the neighbouring town), and a village under the GeoNames
population floor is unknown to the towns list. So a hint, never a refusal.

## To do

1. In the editor, when the name typed matches a GeoNames town within about 10 km of the place
   (`town_key` folding, as the folder guess), a hint under the name: "Blankenberge is a town:
   `classify` already names its photos. Keep it as a place only for exact borders (an
   OpenStreetMap area) or another name." The save still works.
2. In "Your places", such a place carries a discreet mark (ⓘ, the same sentence as tooltip).
3. The page's intro line says in one sentence what a place is for (home, the grandparents',
   the office), and that towns are named on their own.
4. Tests: the hint for a town nearby, none for "Geer chez papy", none for a town of that name
   on another continent.
5. `i18n_update`; docs EN + FR (`commands/places.md`: "a place, not a town"); `docs_screenshots`
   to run.
