# 0646 — Events grouping preview: the trips too, and only the photos classify works on

- **Priority**: Low
- **Batch**: settings-on-pages
- **Depends**: —
- **Files**: `src/media_hygiene/review/setting_groups.py`, `src/media_hygiene/classify/`

## Problem

Follows 0643 (commit cfbcd53c, 178 ms measured on 50 000 synthetic photos). The preview does not
show trips (`trip_min_km` is only checked: trips need the home place and the towns) and covers the
whole index rather than the photos classify works on.

## Decided (2026-11-07, maintainer, review of the iterate of 2026-11-06 (3))

Both: the trips previewed, and the scope of classify. Slower is accepted (over 1 s *estimated*);
the page says it is working.

## Acceptance

- [ ] Moving `trip_min_km` shows the trips that appear or disappear, nothing written
- [ ] The preview counts the same photos as the real classify (test comparing both)
- [ ] Measured: preview time on 50 000 photos, gazetteer loaded (*measured*)
