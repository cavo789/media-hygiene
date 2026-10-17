# 0212 — Bursts: the ⭐ shot is the one whose faces are sharpest, when `people` has looked at them

- **Priority**: Low
- **Batch**: review-bursts
- **Depends**: —
- **Files**: `src/media_hygiene/plan/bursts.py`, `src/media_hygiene/plan/burst_proposals.py`, `src/media_hygiene/plan/face_scores.py` (new), `src/media_hygiene/index/face_rows.py`, `src/media_hygiene/services/audit_analysis.py`, `src/media_hygiene/review/views.py`, `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/test_burst_proposals.py`, `tests/unit/test_similar.py`, `documentation/en/clean/10-review-bursts.md`, `documentation/fr/clean/10-review-bursts.md`, `documentation/en/reference-people.md`, `documentation/fr/reference-people.md`

## Context

Chosen by the maintainer on 2026-10-17 (proposal F7). A burst's ⭐ is the sharpest whole frame;
step 10 says it plainly: "it measures blur only, not a closed eye". In a portrait burst, the
sharpest frame may be the one with a sharp background and a blurred face. Excire Foto 2025 picks
the best shots by eye sharpness (vendor, 2026-10-17).

`people` already measures each face's sharpness — the variance of the Laplacian of the aligned
face, the same function as the frame's (`faces/engine.py`, `sharpness_of`) — and keeps it in the
index (`faces.sharpness`). Measured on the maintainer's index (2026-10-17): 27,159 faces on 50,523
photos looked at.

## What to do

- For a series whose every shot was looked at by `people` (a `face_scans` row of its current
  version) and where at least half of the shots have faces: rank the shots by the sharpness of
  their main faces — the least sharp of the faces at least half as large as the shot's largest
  face, so that every main face must be sharp — then by the frame's sharpness. A shot without a
  face comes after those with faces. Any other series: as today.
- The proposals aside (`[review] propose_aside_below`, `identical_below`) use that score; the
  reason under a picture says it ("faces sharpest", "faces less sharp: 30 % of the best").
- The audit reads the face rows of the burst shots only (one query, `index/face_rows.py`); it
  never runs the face models.
- Size caps: `review/views.py` (194/200), `index/face_rows.py` (188/200) and
  `plan/burst_proposals.py` (181/200) are nearly full: the face score and its index query go to a
  new `plan/face_scores.py`, the page's wording to a new module if needed.
- The "half as large" share is a constant, not a setting (an internal heuristic): say so in the
  report.

## Explicit non-goals

- Closed eyes: another model, its licence to check first.
- Running `people` from `review`: the faces come from the index or not at all.

## Acceptance

- Unit (synthetic face rows): in a series, a shot with one blurred main face among sharp ones
  loses the ⭐; a series not fully looked at keeps today's order; a shot without faces comes after
  those with faces; the proposals and their reasons follow the score.
- The review page shows the reason; docs both languages (step 10: the ⭐ follows the faces once
  `people` has run; the people reference: one more use of the faces). Say in the report that
  `docs_screenshots` should run.

## Gain (estimated)

Portrait bursts: the ⭐ and the proposals follow the faces instead of the whole frame — for the
photos `people` has looked at (on the maintainer's collection, all of them: 50,523 photos looked
at, measured 2026-10-17).
