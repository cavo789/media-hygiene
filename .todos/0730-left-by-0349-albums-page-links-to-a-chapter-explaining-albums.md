# 0730 — What 0349 left: The albums page links to a chapter that explains albums and the page

- **Priority**: Medium
- **Batch**: backlog
- **Depends**: —
- **Files**: `.todos/DONE/0349-albums-page-links-to-a-chapter-explaining-albums.md`, `src/media_hygiene/share/templates/album.html.j2`, `src/media_hygiene/share/album_page.py`, `src/media_hygiene/review/page_header.py`, `src/media_hygiene/cli/menu_catalog_share.py`, `.config/mkdocs/mkdocs.yml`

Split from section 0349 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0349-albums-page-links-to-a-chapter-explaining-albums.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The shared header's documentation links and the catalog `doc` of "Your albums" (it is a `Group(extra="albums")`, not a `Step`).
- `/albums` (empty or not, PC and paired phone) shows a documentation link that opens the new
- `tests/unit/test_documentation.py` and `test_docs_site.py` pass (links, parity, nav).

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.
