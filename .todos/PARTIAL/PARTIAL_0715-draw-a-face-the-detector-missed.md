# 0715 — Draw a face the detector missed, then look for that person

- **Priority**: Low
- **Batch**: people
- **Depends**: 0714
- **Files**: `src/media_hygiene/person/app.py`, `src/media_hygiene/person/second_look.py`, `src/media_hygiene/faces/align.py`, `src/media_hygiene/faces/engine.py`, `src/media_hygiene/person/templates/person.js.j2`, `documentation/en|fr/commands/people.md`
- **Needs maintainer**: a few real photos where a known person's face is visible but not detected (paths only), to measure how often a drawn box gives a usable likeness

Follow-up of 0714 (step 5 of the 2026-11-12 discussion). Some faces are never on the people
page: not detected, or below `[people] min_face` (40 px) / `min_sharpness` (30)
(`people/recognisable.py`). On `/person` the user sees the person but there is nothing to
click.

## Proposal

- On `/person`, "Draw a face": the user drags a box on the photo; the tool runs the detector
  on that crop at a larger scale first (`second_look` already looks again), and, if still
  nothing, aligns the box itself and computes its embedding.
- The box's face is then named and searched exactly like a detected one (0714): its photos
  closest first, confirmed by selection.
- Its likeness says how sure it is: a hand-drawn face below a confidence threshold says "too
  small or blurred to find others" rather than showing noise.
- Stored like a detected face, flagged `drawn`, so a later audit does not drop it.

## Open questions

- Should a face below `min_face`, drawn by hand, be kept for search at all? Measure on the
  maintainer's photos first (Needs maintainer).
- Threshold: a constant first; a setting only if collections differ (few-settings rule).

## Tests

- A drawn box on a synthetic face returns that face's other photos.
- A drawn box on a blank area says nothing usable was found, writes nothing.
- A drawn face survives a re-audit of the photo.

## Status — PARTIAL (2026-11-12)

### Done
- `/person`: "✏ Draw a face the tool missed": drag a box; second-look detection on the enlarged area, else the box aligned and embedded (`faces/boxed.py`, `person/drawing.py`, `person/draw_route.py`, `person_draw.js.j2`).
- Usable face stored in `faces` (number ≥ `DRAWN_FROM` = 1000, no schema change), named and searched like a detected one; survives a re-audit of the same photo version (`index/drawn_faces.py`, `index/face_rows.py`).
- Below threshold or blank area: "Too small or blurred to find others…", nothing written.
- Provisional decision: a drawn face below `min_face` is kept for search, not shown on the people page.
- Tests `tests/unit/test_drawn_faces.py`, `test_person_route.py`; docs EN/FR `people.md`, `person.md`; FR 100 %.

### Not done
- Measuring the thresholds `DRAWN_SIDE = 20` px, `DRAWN_SHARPNESS = 15` (estimated: half of `min_face`/`min_sharpness`).
  **Reason:** needs the maintainer: ~10 real photos with a known person's missed face, box drawn on `/person`, note whether that person's photos come first; a small log of each drawn face's sharpness and score still to add.
- Dialog not checked in headless Chromium; `docs_screenshots` not run.
- Open question: mark drawn faces on the people page?
