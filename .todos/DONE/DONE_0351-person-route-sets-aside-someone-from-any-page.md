# 0351 — Every page: "Set this person aside" from a photo, or from a typed path

- **Priority**: High
- **Batch**: people
- **Depends**: 0328, 0329
- **Files**: `src/media_hygiene/review/shared_routes.py`, `src/media_hygiene/people/person_route.py`, `src/media_hygiene/people/person_faces.py`, `src/media_hygiene/people/aside.py`, `src/media_hygiene/faces/engine.py`, `src/media_hygiene/faces/detect.py`, `src/media_hygiene/review/templates/pick_viewer.html.j2`, `src/media_hygiene/review/templates/pick_viewer.js.j2`, `src/media_hygiene/people/templates/person.html.j2`, `tests/integration/people/test_person_route.py`, `documentation/en/commands/people.md`, `documentation/fr/commands/people.md`

## Why

The maintainer, 2026-10-24, on `mh review` (burst series 608 of 1119): two photos of a person
they had set aside days before, through their group on `mh people`, are still there
(`C:\Photos\Manon 2023\dcim\20221031_220832.jpg` and `…_220833.jpg`). They want, from any page
(`review`, `browse`, …), to say "this person: set all their photos aside", and to be able to
paste a photo's path to find that person.

Why these photos escaped (measured 2026-10-24, read-only: the volume `media-hygiene-cache`
mounted `:ro` in a throwaway `media-hygiene:latest` container, SQLite opened with
`?mode=ro&immutable=1`, nothing copied): both photos are in `face_scans` with **0 faces**. The
detector (YuNet, on the upright picture only) found no face. The photos are tilted by about
30° and blurred by motion. So the set aside was not wrong: these photos never had a face to
compare. They could not join any group, and 0328's "look alike" section would not find them
either.

Also measured: the cache parks 5,220 face rows from 19 clean runs (2026-10-17 → 2026-10-24),
which 0328 can keep as remembered faces.

## What

- **A shared route `/person`**, served by every page like `/docs/` (`review/shared_routes.py`):
  the same feature in the same place on every page (decided 2026-10-24: option B, rather than a
  link that would need `mh people` running next to the page).
- **How to enter it**:
  - a button "👤 Set this person aside" in the shared large view (`pick_viewer`, skill
    `photo-picking-pages`: the same bar and keys on every page), and on the `review` tiles;
  - a field on `/person` where you **paste a path**: `C:\Photos\…\x.jpg` (mapped to
    `/data/c/…` with `paths/`), or `/data/c/…`. An unknown path, or one outside the mounts, gets
    one sentence saying why, never an error.
- **Precise lookup**: the faces of *that* photo, from the index (`faces` rows, by path):
  - several faces: their crops are shown, you click the right one;
  - one face: straight to that person.
- **No face in the cache for that photo** (this case): the page asks before analysing
  **only this photo** again, slower but more tolerant: the picture rotated (±30°, ±90°) and
  without the `min_sharpness` / `min_face` filters. The faces found are shown to pick from,
  never stored as the photo's usual faces (the regular detection stays the same for every
  photo). If nothing is found either, one sentence says so and offers 0329's "set this photo
  aside". Whether rotating finds these two photos is **to measure** (synthetic tilted faces in
  tests; the two photos above, read-only, by the maintainer through `mh-measure.ps1` if needed),
  not promised.
- **The person view**: the photos of that face's group, plus those coming close to it (0328's
  looser threshold, including faces left out of the groups) and the remembered face it matches
  if any ("looks like the person set aside on <date>"), shown as tiles following
  `photo-picking-pages` (all picked, × to leave one out). "Set these n photos aside" writes the
  decisions file like `POST /api/aside`, read back from the disk and the sentence shown, and the
  face is remembered (0328) so that photos added later are offered next time.
- Faces not computed yet (`audit --people` never run): the page says so in one line with the
  command to paste (whether it needs the 🤖 flag like other model-backed commands: to check
  against the convention).
- What happens when files move: everything is looked up by the photo's current path in the
  index; the remembered faces carry no path (0328).

## Tests

- Integration: a photo with two faces → two crops, the chosen one leads to its group; a typed
  `C:\…` path finds the same photo; a photo without faces → the slower analysis is offered, a
  synthetic face tilted by 30° is found by it; "Set aside" lands in `chosen` and is read back.
- Every page serving `/person` (one test over the page apps, like `/docs/`).
- Docs en + fr (`people` page and the pages that gain the button); captures stale →
  `docs_screenshots`.
