# 0318 — `search`: "Why this name?" shows the face, its nearest reference and the score, then lets the user correct it

- **Priority**: Medium
- **Batch**: people
- **Depends**: 0317
- **Files**: `src/media_hygiene/people/naming.py`, `src/media_hygiene/people/crops.py`, `src/media_hygiene/search/app.py`, `src/media_hygiene/search/templates/search.js.j2`, `src/media_hygiene/search/templates/search.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/search.md`, `documentation/fr/commands/search.md`, `documentation/en/reference-people.md`, `documentation/fr/reference-people.md`, `tests/integration/test_search_why_name.py`

## Why

The maintainer, 2026-10-23: "it would help to understand, because `mh` users cannot talk with
you as I do. But it must also allow correcting, like the × (0317)."

To explain the two wrong "Marie Saive" names that day, Claude had to run a script over the
index and cut out the faces. Then it was clear: on `IMG_20180517_203027.jpg` the name came from
the **man in profile**, not the woman the maintainer suspected (0.413 against a Marie Saive
photo taken with an old compact, threshold 0.363). Without seeing the face, a user assumes the
wrong person and cannot fix it.

## What

A click on a `person` chip itself (not its ×) opens a small panel over the card or the large view:

- the face cut out of this photo (`people/crops.face_crop`, served as on the people page,
  never written to disk), with its box outlined on the photo when several faces;
- **how** it got the name: *confirmed by you* or *close to a face you confirmed*;
- for an assigned face: the nearest reference cut out, with its folder and file name (a link
  that opens it in the large view), and the score said in words with the number, e.g.
  "resemblance 0.41, a name is given from 0.36 (`[people] similarity`)". Show the next nearest
  person too when it is close (within 0.03), because that is often what the user expects;
- two buttons: **Not {name}** (same route as the ×, 0317) and **Yes, it is {name}** (adds the
  face to `faces`: confirmed, then it becomes a reference). Each one is saved, read back from
  disk and shown with `proof_line`.

The data comes from `name_all`: return, next to each `FaceName`, the reference id and the score
that decided it. This must cost nothing when no one asks: compute the panel's data on demand
(`GET /api/people/why?face=<id>`) for one face, not for every hit.

## Tests

- An assigned face: the panel's JSON names the nearest reference id, the score, the threshold.
- A confirmed face: *confirmed by you*, no score.
- **Yes**: the face id is in `faces` of the person file, read back; **Not**: in `rejected`.
- The panel opens with the keyboard too (from the large view), and Esc closes it without
  touching the picking (skill `photo-picking-pages`).

## Docs

`commands/search.md` and `reference-people.md` (both languages): what "close to a face you
confirmed" means, how to read the score, when to raise `similarity`. Say that
`docs_screenshots` should run.

## Later, not here

Whether `similarity = 0.363` (SFace's figure for comparing *two* faces) is too low when the best
of thousands of references is kept (3,615 on the maintainer's index, measured 2026-10-23):
measure the wrong names per threshold on real photos before changing the default
(skill `measure-before-ranking`).
