# 0701 — Every tile page keeps its pictures in the browser across runs, as the library does

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/person/pictures.py`, `src/media_hygiene/people/pictures.py`, `src/media_hygiene/places/photos.py`, `src/media_hygiene/review/local_app.py`, `src/media_hygiene/share/`, `src/media_hygiene/slideshow/pictures.py`, `src/media_hygiene/search/stable_pictures.py`

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0673 (commit fa1ed2ba) named the library's tiles by file version (`/thumb/<key>.<tag>.jpg`,
immutable). People, person, places, the reviews, albums (and the album link door) and the TV
keep the per-run ETag. Decided: one TODO for all of them, reusing `search/stable_pictures.py`.
The three limits of 0673 are accepted (same size and date, a move outside the tool shown until
the next audit, a rendering change needs the version bump).

## Acceptance

- [ ] Each page's pictures under the stable names; faces may keep their rule (said)
- [ ] One test per invalidation event, as in `tests/unit/test_stable_pictures.py`
- [ ] The album link door (`review/doors.py`, number-only keys) and the phone allow-list updated
