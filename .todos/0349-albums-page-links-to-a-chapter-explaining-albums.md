# 0349 — The albums page links to a chapter that explains albums and the page

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: 0342
- **Files**: `src/media_hygiene/share/templates/album.html.j2`, `src/media_hygiene/share/album_page.py`, `src/media_hygiene/review/page_header.py`, `src/media_hygiene/cli/menu_catalog_share.py`, `documentation/en/`, `documentation/fr/`, `.config/mkdocs/mkdocs.yml`

## Context

Reported by the maintainer (2026-10-24, screenshot of `127.0.0.1:8088/albums`, empty state): the
page offers no link at all to the documentation, so a user cannot learn what an album is nor what
the page does. 0342 brings the shared header (whose documentation links come from the catalog's
`doc` of the action, `page_header.py` → `served_url`), but there is no chapter to point at:
`documentation/*/sort/12-albums.md` and `commands/album.md` explain the **hard-link** albums of
`mh album`; nothing in `documentation/` describes the albums built from `search`/`browse`
(*Add to the album*, `services/album_logical.py`), the `/albums` page, or its use from a phone
paired by `mh --lan` (measured: `grep -rn "/albums\|Add to album" documentation/en` → no hit).
The "Your albums" group of `menu_catalog_share.py` carries no `doc` either.

## To do

- Write the chapter (en + fr, same file name): what an album is here (a list of photos, the files
  are only read, nothing copied or moved), how to fill one from `search`/`browse`, what `/albums`
  shows and allows (remove a photo, add it to another album — only the albums file changes), from
  the PC and from a paired phone; how it differs from the hard-link albums of step 12, with a link
  both ways. Add it to `nav` of `mkdocs.yml`.
- Give the "Your albums" action its `doc`, so the shared header of 0342 links to it (the chapter
  in the page's language, and the other one).
- The empty state ("No album yet…") ends with a link to that chapter (served `/docs/` on the PC
  and on the phone, via `served_url`).
- Screenshots: synthetic pictures only (`tests/support/docs/`).

## Acceptance

- [ ] `/albums` (empty or not, PC and paired phone) shows a documentation link that opens the new
      chapter, in French on a French page.
- [ ] `tests/unit/test_documentation.py` and `test_docs_site.py` pass (links, parity, nav).
- [ ] `docs_screenshots` to run (new chapter, album captures).
