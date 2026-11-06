# 0643 — Events grouping setting: the events shown changing before it is kept

- **Priority**: Low
- **Batch**: settings-on-pages
- **Depends**: —
- **Files**: `src/media_hygiene/review/setting_groups.py`, `src/media_hygiene/classify/`

## Problem

Follows 0606 (commit d1bf8ed2). The grouping (`merge_gap_hours`, `min_event_size`,
`trip_min_km`) is set without a preview: the list changes at the next classify only.

## Decided (2026-11-06, maintainer, review of the iterate of 2026-11-06 (2))

A dry-run preview: the events as they would be, before saving (rule *Seeing first*).

## Acceptance

- [x] Moving a value shows the events that merge or split, without writing anything
  (*See the events first* in the grouping section: `POST /api/events/grouping`,
  `classify/grouping_preview.py`, `search/grouping_desk.py`; counts before/after, merged,
  split, new, gone, 12 listed per kind). The trip distance is checked, not previewed (trips
  need the home place and the towns of a classify run): said on the page.
- [x] Measured: 178 ms per preview (best of 5) on a synthetic in-memory index of 50 000
  dated photos, devcontainer, `nice -n 19` (SQL read + parse + both cuts + compare).
