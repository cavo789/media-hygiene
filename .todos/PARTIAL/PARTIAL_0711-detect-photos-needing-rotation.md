# 0711 — Detect photos shown sideways (no EXIF orientation) and offer to turn them

- **Priority**: Medium
- **Batch**: slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/scan/visual.py`, `src/media_hygiene/scan/exif.py`, `src/media_hygiene/faces/`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/review/` (new page), `src/media_hygiene/actions/`, `documentation/en|fr/`

Reported by the maintainer on 2026-11-11 after a one-hour random show on the TV.

## Context

The slideshow already applies the EXIF orientation (`slideshow/screen_jpeg.py`). Photos
still shown sideways carry no orientation tag: scans, pictures passed through a messaging
app or an editor that dropped it. Only the pixels can tell.

## Proposal

1. **Which files** — only camera photos, never screenshots, game captures, drawings,
   scans of documents or collages (two of the three wrong turns measured below were not
   photos: a video-game dog, a collage):
   - the EXIF says a camera took it (`camera` of `VisualFacts`: make or model present);
   - and its make is not a games console or a screenshot tool (a short list of makes, e.g.
     `Nintendo`: `HNI_0012 (6).JPG`, A15, is likely a Nintendo 3DS capture — *not checked*:
     read its EXIF before writing the list); names of screenshots (`name_patterns`) left out;
   - photos without any camera EXIF (WhatsApp, scans) are left out of the first version;
     a later TODO may add them once measured.
2. **The guess** (at audit time, in the worker that already decodes the photo; cached in
   the index with the other visual facts, schema bump; only for photos whose tag is none,
   `0` or `1`):
   - faces found in the 4 turns (existing YuNet), the turn with the best total score;
   - proposed when the best turn finds faces and the stored one finds none (measured: every
     turn proposed had 0 faces as stored, so a score margin separates nothing);
   - **180 deg only when two faces or more agree** (2 of the 3 errors were 180 deg; cameras
     seldom store a photo upside down without a tag).
   - Also read the tags `90` / `180` written in degrees by some software (12 photos):
     treated as the EXIF codes 6 / 3 everywhere pictures are shown upright.
3. **Seeing first** (0524): a page "Photos to straighten", tiles from the shared `pick_*`
   templates (skill `photo-picking-pages`), each tile shown as it would be after the turn;
   untick to refuse (refusals remembered, not proposed again); *Apply now* (`ApplyOffer`).
4. **The turn**: lossless — write the EXIF orientation tag (the pixels are not touched),
   journaled like the other writes, undone by `undo`; protected folders never written.
   The index, previews and thumbnails follow (new mtime: new preview key).
5. Entry points: a line of the audit's "What next" when some are found, the home page's
   card, the docs (`commands/` page or a section of an existing one, both languages).
6. The slideshow does not guess at display time (a wrong turn on the TV is worse than a
   photo shown sideways): it shows the photos once turned.

## Acceptance

- Step 48 of `mh-measure.ps1` with the rules (done 2026-11-12, see below): 21 of 22 right.
- A screenshot, a console capture, a collage and a person lying down in the tests (synthetic
  pictures with a fake face finder): none proposed.
- Turn, then `undo`: the file is byte-identical to before; the thumbnail follows.

## Measured (maintainer's PC, `mh-measure.ps1` step 48, 2026-11-11)

- Orientation tags of 38,438 pictures (headers read in 88 s): `1` 25,147; `6` 5,522; none
  4,203; `0` 2,413; `8` 496; `3` 209; **`90` 10 and `180` 2** (degrees written by some
  software instead of the EXIF codes: not applied today, worth reading too); unreadable 436.
- Untagged (none or `1`; `0` was left out of that run): 2,237 guessed in 300 s, **0.13 s per
  photo** (4 detections, decode at 1280 px). 33 would be turned (1.5 %).
- By eye: of those 33, **30 turned right, 3 wrong** (A15 a cartoon dog turned 180 deg: an
  animal's head taken for a face; A16 a collage of photos in several directions, 180 deg;
  A18 a girl lying down on an upright photo, 270 deg); 20 photos with faces left as they
  are: **0 missed**.
- *Estimated* for the whole collection: ~29,350 untagged + 2,413 tagged `0` → about 470
  sideways photos with faces (1.5 %); 31,800 × 0.13 s = ~69 min on one core, once (the
  index keeps the answer), ~17 min on 4 workers. Photos without faces: not measured (the
  guess says nothing on them).

So: faces are reliable enough to **propose** (91 % right among those flagged), never to
apply blindly — the page that shows them before Apply stays mandatory (3 in 33 wrong).
Rules for the guess, from the three errors: propose 180 deg only when two faces or more
agree (2 of the 3 errors were 180 deg; cameras seldom store upside down untagged), and only
when the best turn beats the stored one by a clear margin (a person lying down).
Also read the tags `90`/`180` (degrees) some software wrote: 12 photos.

## Measured again with the rules (step 48, 2026-11-12, maintainer's PC)

- Camera photos only: 3,331 untagged pictures left out (no camera, a console — the 820
  `Nintendo 3DS` captures —, a screenshot); 28,432 kept.
- 2,093 guessed in 300 s (0.14 s each): **22 proposed, 21 right, 1 wrong** (A12 =
  `P1020877.JPG`, the same girl lying down as the day before); 20 left as they are: 0
  missed; the 180 deg rule left out none of this sample (the cartoon dog and the collage
  were already out as non-camera pictures).
- Scores: every proposed turn had **0 faces as stored** and 1–3 faces turned (≈0.9 per
  face); the wrong one too. No margin can tell it apart.
- Tried and rejected (measured by Claude on `/mnt/c/Photos`, read-only, 2026-11-12): trust
  the "no turn" of camera models that wrote turned tags elsewhere (they have a sensor).
  The wrong one's `Panasonic DMC-FX37` has a sensor (249 turned of 4,473) — but so has the
  `SAMSUNG WB700` of several right turns (231 of 6,780): the rule would lose them.
- So a person lying down stays the guess's blind spot (≈1 in 22): the page that shows each
  turn before *Apply now*, with an untick remembered, is the answer — no extra rule.

## Status — PARTIAL (2026-11-12)

- **Done:** the guess itself, pure and tested — `src/media_hygiene/faces/straighten.py`:
  `worth_guessing` (camera make present, not `Nintendo*`, not a screenshot, orientation tag
  none/`0`/`1`), `proposed_turn` (no face as stored, best turn has faces, 180 deg only with
  2+ faces), `guess_turn` (4 turns through any face counter), `ORIENTATION_OF` (turn → EXIF
  code 6/3/8). Tests `tests/unit/test_straighten.py` with a fake finder: screenshot, console
  capture, collage (no camera), person lying down with a face as stored: none proposed.
- **Not done:**
  - Call it in the audit worker and cache it (index schema bump, invalidation: new mtime
    after a turn = new row; a refusal kept by path must follow `sort`/`undo`/renames).
  - Degree tags `90`/`180` read as 6/3: changing `upright_picture` alone would shift the
    cached face boxes and visual facts of those 12 photos and leave old previews sideways;
    it needs a preview `_VERSION` limited to them or an index re-read of those rows.
  - The "Photos to straighten" page (`pick_*`, Apply now), the journaled lossless tag write
    + `undo` (byte-identical check), audit What next line, home card, docs EN/FR.
  - **Reason:** out of one session's scope; each remaining part is independent of the rules.
