# 0322 — `mh phone`: the folders a gallery app makes outside `DCIM` (`Pictures/…`)

- **Priority**: Low
- **Batch**: phone
- **Depends**: —
- **Needs maintainer**: the folders of their phone outside `DCIM` that hold photos (names only)
- **Files**: `tests/measure/mh-measure.ps1`, `src/media_hygiene/services/phone_plan.py`, `src/media_hygiene/services/phone_journal.py`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`

## Why

0312 (2026-10-23) checked: `mh phone` lists only the phone's `DCIM` (`phone_plan.py`, "below
DCIM"; `phone_journal.py` rebuilds `<phone>\DCIM\<path>`). A folder sorted by a gallery app
(Samsung Gallery's albums, `Pictures/Surricate`) may live outside it: neither imported nor
offered to free. The phone page now says so in its legend.

## What

1. Measure first (a step in `mh-measure.ps1`): which top folders of the maintainer's phone hold
   photos or videos, and how many files.
2. If some do: list them too (a `[phone] folders` setting, `DCIM` by default?), the plan's paths
   relative to the phone's root instead of `DCIM` — which changes the decisions file and the
   journal's paths: write what an old `phone-decisions.json` becomes.
