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

- [ ] Moving a value shows the events that merge or split, without writing anything
- [ ] Measured: preview time on a synthetic library of 50 000 photos (*measured*)
