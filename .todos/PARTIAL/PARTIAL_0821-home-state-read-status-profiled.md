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

## Status — PARTIAL (2026-11-14, second pass)

### Measured on the maintainer's PC (step 46, 616 report folders, 611 journals)
- `home_state` 2.14 s / 1.79 s: `read_runs` 0.49 / 0.30 s (one `stat` per journal, facts
  cached already), `load_summaries` 0.47 / 0.21 s and `report_folders` 0.22 / 0.26 s (the
  same 616 `summary.json` read **twice**), `sort_state` 0.15 s (a third glob of the 616
  folders), `tag_coverage` 0.08-0.10 s; the rest under 50 ms.

### Done
- The reports are read once per state: `read_status` keeps them (`Status.reports`) and
  `latest_reports` links from them. Test `test_home_reports_read_once.py`; 315 tests of the
  changed modules and importers pass. Gain *estimated* from the figures above: 0.21-0.26 s
  of 1.8 s (-12 to -14 %).

### Not done
- Step 46 again after this change. **Reason:** maintainer's PC only.
- `sort_state`'s own glob (0.15 s) and `read_runs`' 611 stats (0.3 s, also paid by the
  safety card): the floor is one `stat` per file through Docker Desktop; going lower means
  fewer files. **Reason:** a decision for the maintainer: 616 reports and 611 journals are
  kept forever unless `mh reports --prune N` is typed — an automatic retention (a setting?)
  would cut every one of these costs in proportion.
