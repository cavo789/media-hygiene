# 0720 — People page: Invert selection over faces, a bar button and Ctrl+I

- **Priority**: Medium
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/people/templates/people_sections.js.j2`, `src/media_hygiene/people/templates/people_face_band.js.j2`, `src/media_hygiene/people/templates/people.html.j2`, `tests/unit/test_people_page.py`

Follows PARTIAL 0716 (`.todos/PARTIAL/PARTIAL_0716-people-page-rectangle-and-select-all.md`, commit c8570e57), which gave the people page a rectangle selection and Ctrl+A over faces but no Invert (the key `i` already means *ignore the group* there).

Decided by the maintainer in the review of 2026-11-12.

## What

- A bar button *Invert selection* (same place and wording as the shared `pick_*` bar, skill `photo-picking-pages`) and the key **Ctrl+I**; `i` alone stays *ignore the group*.
- Acts on the faces visible in the current section only (never on hidden ones).
- The keys panel lists Ctrl+I; French strings via `i18n_update`; the people documentation page EN + FR mentions it.

## Acceptance

- [ ] Button and Ctrl+I invert the picked faces of the current section; `i` still ignores the group (test).
- [ ] Headless Chromium check like 0716's.
- [ ] Docs EN + FR; say that `docs_screenshots` should run if the bar changes.
