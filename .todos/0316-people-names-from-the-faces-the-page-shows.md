# 0316 — Names come only from faces the people page shows: `min_face` and `min_sharpness` everywhere

- **Priority**: High
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/people/naming.py`, `src/media_hygiene/search/people_words.py`, `src/media_hygiene/services/people_names.py`, `src/media_hygiene/services/people_groups.py`, `tests/unit/test_people_naming.py`, `tests/unit/test_search_people_words.py`, `documentation/en/reference-people.md`, `documentation/fr/reference-people.md`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

## Why

The maintainer, 2026-10-23: `search` showed "Marie Saive" under
`C:\Photos\2014\Juillet 2014\HNI_0099.JPG`, a class photo where she is not. Measured that day
(read-only script over the volume `media-hygiene-cache` and `config.toml`): the photo's 6 faces
are 27–32 px and blurry (sharpness 5.5–13.1). Face `#2`, a boy, is nearest to a Marie Saive
reference at 0.378, above `similarity = 0.363`, so it is *assigned* her name. With
`min_face = 40` and `min_sharpness = 30`, these faces are never shown on the people page,
so the user cannot see or correct them.

There is one `[people]` section, read the same way by every command. What differs is the code
that reads it: `group_people` (`services/people_groups.py`) drops faces that are too small or
too blurry before grouping, but `name_all` (`people/naming.py`) names every face of the index. Its
callers are `people_words` (search, classify `person` rule, inventory, XMP tags in
`services/xmp_plan.py`) and `named_photos` (the counts at the end of a `people` run). The
maintainer's rule: the same setting must mean the same thing everywhere.

Measured on the maintainer's index (2026-10-23): 615 of 15,754 assigned faces are hidden this
way. **576 photo + name pairs (≈ 3.8 % of 14,998) exist only through them**, so they are
names nobody can check, and some of them get written into XMP sidecars.

## What

- One predicate, in `people/naming.py` or next to it, e.g. `recognisable(face, settings)`:
  side ≥ `min_face` and sharpness ≥ `min_sharpness`. `group_people` and `name_all` both use
  it, so the rule cannot drift again.
- `name_all`: a face that is not recognisable gets `NOBODY`, unless it is **confirmed**. A
  confirmed face keeps its name, because the user said so. `Known` needs the thresholds, so
  carry them on `Known` (built from `PeopleSettings` already).
- An ignored reference still ignores: no change.
- The end-of-run counts (`named_photos`) and `search` then agree with the page.

## Tests

- A 30 px face close to a reference: no name; the same face confirmed: named.
- A sharp 60 px face: named, as today.
- `min_face = 0`, `min_sharpness = 0`: every face is named, as before (regression guard).
- `people_words` and `named_photos` give the same photos for one person as the page's
  verified + attributed sections (one fixture, three readers).

## Docs

`reference-people.md` (both languages): `min_face` / `min_sharpness` decide which faces count
at all, not only which are grouped. `commands/people.md` "Bon à savoir" says "ne changent que
le regroupement": correct it in both languages.

## Report

Before → after on the maintainer's index: assigned pairs that cannot be checked go from 576 to 0
(re-run the count script described above).
