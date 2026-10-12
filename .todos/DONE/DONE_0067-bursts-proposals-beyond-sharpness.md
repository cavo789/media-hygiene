# 0067 — Bursts: proposals beyond sharpness (near-identical shots, missed exposure)

- **Priority**: High — makes the obvious series of the batch validation far more numerous
- **Batch**: review-bursts
- **Depends**: —
- **Files**: `src/media_hygiene/plan/bursts.py`, `src/media_hygiene/plan/likeness.py`, `src/media_hygiene/plan/similar_models.py`, `src/media_hygiene/review/views.py`, `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/config/review_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`

## Context

Filed from the 2026-10-10 usability review. A shot is proposed aside only when far less
sharp than the sharpest one. Many series are five nearly identical frames of the same
scene: none is blurry, all are kept, the user has to decide by hand. The facts needed are
already in the index (`VisualFacts` pHash/dHash, `MediaMetadata.exposure`).

## Proposal

- **Near-identical shots**: shots whose pHash distance to a sharper shot of the series is
  below `[review] identical_below` → proposed aside, the sharpest kept.
- **Missed exposure**: a shot clearly over- or under-exposed compared with the others
  (clipped share / mean brightness) → proposed aside.
- Each proposed shot shows its reason under the picture ("nearly identical to #2",
  "overexposed", "blurrier"); the reason goes into the page data only, never into
  `decisions.json`.

## Acceptance

- Unit tests for both reasons and their thresholds (0 disables); the page shows reasons;
  config template and docs en/fr updated.
