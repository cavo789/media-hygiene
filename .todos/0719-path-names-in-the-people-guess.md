# 0719 — Use the names in folders and file names when the tool guesses who a face is

- **Priority**: Medium
- **Batch**: people
- **Depends**: 0714
- **Files**: `src/media_hygiene/people/suggest.py`, `src/media_hygiene/people/known.py`, `src/media_hygiene/person/templates/person_paths.js.j2`
- **Needs maintainer**: a measurement on the real collection (how often the path's name is right when it differs from the guess)

Asked by the maintainer on 2026-11-12: two sisters (Manon, Chloé) look alike as babies and the
tool often guesses "≈ Chloé" on photos of Manon, while the folder (*Avril 2004 - Manon 5 mois*)
or the file (*Petite Manon.png*) says who it is. `/person` now shows that name as a hint
(📁 Manon, red when it differs, and a filter), never naming from it.

## Proposal

- When two people are close for a face (both within the likeness margin), a path that names
  exactly one of them breaks the tie for the ≈ guess (never a ✓: confirming stays a click).
- On the people page, the same 📁 hint on the faces, and the tie broken the same way.
- Not when the path names both (*Manon & Chloé*) or none.

## Open questions

- Measure first: on the maintainer's photos, how often a 📁 name that differs from the guess
  is right (an mh-measure step counting 📁 vs ≈ vs ✓ once some faces are confirmed).
- A name that is also a common word (*Marraine*, *Papy*) in a folder: count them apart.

## Tests

- A face close to Manon and Chloé in *Manon 5 mois* is guessed ≈ Manon.
- *Manon & Chloé* changes nothing; a path naming a third person changes nothing.
