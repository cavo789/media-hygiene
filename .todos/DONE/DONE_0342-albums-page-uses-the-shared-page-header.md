# 0342 — The albums page: the same header as every page, "Back to the home page" on the right

- **Priority**: Low
- **Batch**: share
- **Depends**: 0341
- **Files**: `src/media_hygiene/share/templates/album.html.j2`, `src/media_hygiene/share/templates/album.js.j2`, `src/media_hygiene/share/album_page.py`, `src/media_hygiene/review/templates/page_header.html.j2`, `tests/integration/test_share_album.py`

## Context

Reported by the maintainer (2026-10-24): every page shows *⌂ Back to the home page* at the top
right (`page_header.html.j2`, 0268/0333); `/albums` has its own header with a bare `⌂` at the top
left (`a.back`, `album.html.j2`). One page that differs is a bug (memory: same features at the
same place on every page).

## To do

- `/albums` uses `page_header.html.j2` (brand, page name, documentation links, *Back to the home
  page*), kept usable at phone width (the albums page is phone-first, 0297): the header must wrap
  or shorten on 360 px, never scroll sideways.
- Inside an album, *← Albums* (back to the list) stays a page control, below the header.
- On a phone paired by `mh --lan`, check what *Back to the home page* does (the home page is the
  PC's; the phone may show the phone home of 0269 instead) — to decide, say it in the feedback.

## Acceptance

- [ ] Same header, same place as `search`/`people` on the PC; nothing overflows at 360 px.
- [ ] `docs_screenshots` to run (album captures).
