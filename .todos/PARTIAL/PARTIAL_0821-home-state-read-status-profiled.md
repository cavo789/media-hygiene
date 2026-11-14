# 0821 — Home page: `read_status` and `latest_reports` profiled, then made cheap

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/services/status.py`, `src/media_hygiene/cli/home_state.py`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: step 46 of `mh-measure.ps1` before/after (Windows + Docker Desktop, real tool folders)

Filed 2026-11-14 after 0819 closed.

## Context

*Measured* (step 46, maintainer's PC, real folders, 2026-11-14, after 0819): `GET /api/state`
1.92 s from Windows; inside the container `home_state` 2.07 s then 1.80 s, of which
`read_status` 0.85 / 0.96 s and `latest_reports` 0.45 / 0.20 s (`home_folders`,
`home_pending`, `home_update` ≈ 0). The page is drawn at once from `localStorage` (0692), so
the user sees *updating…* for ~2 s at each opening, on the phone as well; on a first device
the page waits for it. Which part of `read_status` costs the time is **not known yet**
(journals of 83 runs? the index? stats through the bind mount?).

## Proposal

1. Profile first (skill `measure-before-ranking`): extend step 46's timing script to wrap
   the callees of `read_status` (runs listing, each journal read, the index queries) and of
   `latest_reports`, so the maintainer's run says where the second goes. A devcontainer
   profile on the demo tree (`py-spy`) only to cross-check: Docker Desktop's file sharing is
   what makes these slow, synthetic data alone will mislead.
2. Then remove the dominant cost the way 0819 did (what is read through the bind mount for
   nothing, or a cache keyed on stamps already read), listing every invalidation event
   (rule in `workflow.md`).

## Acceptance

- [ ] Step 46 names each part of `read_status` and `latest_reports` (measured, maintainer's PC)
- [ ] `/api/state` under 0.5 s warm on the maintainer's PC, or the reason it cannot be
- [ ] Same state as before (equivalence test), one test per invalidation event if a cache is added

## Status — PARTIAL (2026-11-14)

### Done
- Step 46 of `mh-measure.ps1` also times each part of `read_status` (`status.load_summaries`,
  `read_runs`, `last_walk`, `quarantine_state`, `review_state`, `sort_state`,
  `tag_coverage`, `face_coverage`, `disk_progress`, `mounted_quarantines`) and of
  `latest_reports` (`reports.report_folders`), and counts the report folders and journals
  (line 46g). Checked in the devcontainer on the demo tree (every part listed, read_status
  6 ms there: synthetic data says nothing of Docker Desktop).

### Not done
- The maintainer's run of step 46 with these lines, then the fix of the dominant part.
  **Reason:** the cost only shows through Docker Desktop's file sharing on the real folders.
