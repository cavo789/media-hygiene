# 0768 — What 0671 left: Pages resist hostile names: a test with poisoned file names and EXIF, CSP without `unsafe-inline`

- **Priority**: Medium
- **Batch**: lan-security
- **Depends**: —
- **Files**: `.todos/DONE/0671-pages-csp-without-unsafe-inline-and-hostile-names.md`, `src/media_hygiene/review/http.py`, `src/media_hygiene/review/respond.py`, `src/media_hygiene/i18n/templates.py`, `src/media_hygiene/review/templates/page_frame.html.j2`, `src/media_hygiene/review/templates/home.html.j2`, `tests/support/demo.py`

Split from section 0671 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0671-pages-csp-without-unsafe-inline-and-hostile-names.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The hostile fixture in the demo tree (folder/file/EXIF/XMP/album/person/tag/place names)
- JSON answers are not checked with hostile data (served `application/json` + `nosniff`,
- The hostile fixture walk passes on every page, PC and phone doors
- No `'unsafe-inline'` in `script-src`; the places page's own policy included
- The lint over the 44 sites, exceptions named

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
