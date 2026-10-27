# 0326 — People page: an unnamed group says who it looks like ("Papy?"), one click to confirm

- **Priority**: Medium
- **Batch**: people
- **Depends**: 0324
- **Files**: `src/media_hygiene/people/sections.py`, `src/media_hygiene/people/views.py`, `src/media_hygiene/people/templates/people.html.j2`, `src/media_hygiene/faces/similarity.py`, `tests/unit/test_people_naming.py`, `tests/integration/people/`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

## Why

The maintainer, 2026-10-23, agreed to this proposal while naming people: an unnamed group is
named by typing a first name, even when it is plainly someone already named (a child at another
age, a face seen in another light). The page knows the verified faces of every person: it can
say which one the group comes closest to.

## What

- For each unnamed group, the closest named person: the similarity between the group's faces
  and each person's verified faces (e.g. the median of the best match of each face, to choose
  and measure on synthetic faces), kept only above a floor lower than `[people] similarity`
  (a suggestion, not an attribution) — the floor to measure, not guessed.
- The group's title shows "Looks like Papy? (0.42)" with a button "It is Papy" (= naming the
  group, same request as typing the name) and the key `y` doing the same on an unnamed group;
  a second suggestion when two people are close (siblings).
- A face taken out of someone (`rejected`) never counts towards suggesting them.
- Cost: the vectors are in the cache already; estimate the comparison (groups × verified faces)
  on the maintainer's collection size and keep it out of the page's first answer if slow.

## Tests

- Unit: a group close to a person's verified faces gets their name, one far gets none,
  rejected faces are not used.
- Docs en + fr; captures stale → `docs_screenshots`.

## Setting?

The suggestion floor could become `[people] suggest_similarity`; propose in the report.

## Status — PARTIAL (2026-10-27)

- **Done:** `people/suggest.py` (median of each face's best match against up to 200 verified
  faces per person, 12 faces per group; rejected faces left out; a second name within 0.05),
  "It is Papy? (0.42)" button and `y` on an unnamed group, docs en + fr, unit + integration tests.
- **Not done:** the floor `SUGGEST = 0.30` is **estimated** (below SFace's documented 0.363),
  not measured on real faces; the cost is estimated (about 6 GFLOP for 1,000 groups × 20
  people), not measured on the maintainer's index.
  **Reason:** needs the maintainer's face index: measure the score of right and wrong
  suggestions (and the time of `state()`) with a step of `tests/measure/mh-measure.ps1`, then
  set the floor (or a `[people] suggest_similarity` setting if it must differ per collection).
