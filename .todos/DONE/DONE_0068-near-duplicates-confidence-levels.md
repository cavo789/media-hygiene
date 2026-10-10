# 0068 — Near duplicates: confidence levels, sure groups apart from those to check

- **Priority**: High — more than 500 groups on the real collection, all or nothing today
- **Batch**: near
- **Depends**: —
- **Files**: `src/media_hygiene/plan/near.py`, `src/media_hygiene/plan/near_keeper.py`, `src/media_hygiene/plan/similar_models.py`, `src/media_hygiene/report/near_reasons.py`, `src/media_hygiene/report/csv_near.py`, `src/media_hygiene/report/templates/`, `src/media_hygiene/cli/clean_options.py`, `src/media_hygiene/cli/near_preview.py`, `documentation/en/clean/11-near-duplicates.md`, `documentation/fr/clean/11-near-duplicates.md`

## Context

Filed from the 2026-10-10 usability review. `clean --tier near` moves every near duplicate;
the only check is looking at every group of `near.html`. Many groups are certain (same
stream 🟰, WhatsApp copy with the same EXIF date), a few deserve a look.

## Proposal

- Each group gets a level: **sure** (same stream 🟰; a smaller copy in a messaging/e-mail
  folder with the same EXIF date; perceptual distance 0 and the same camera) or **to
  check** (everything else). The reason joins the 💬 line and a `plan.csv` column.
- `near.html` and the report show the groups to check first, the sure ones folded.
- Console: `480 sure, 20 to look at`.
- **Maintainer decision before coding**: meaning of `--tier near`. Recommended: it moves
  the sure groups plus the groups decided in the browser (the per-group decision TODO),
  and `--tier near-all` keeps today's behaviour. Alternative: keep `--tier near` as is and
  add `--tier near-sure`.

## Acceptance

- Unit tests on the levels; report and CSV show them; docs and captures en and fr.
