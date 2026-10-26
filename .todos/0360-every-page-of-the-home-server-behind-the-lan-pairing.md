# 0360 — Every page of the home server behind the pairing of `mh --lan`

- **Priority**: Medium
- **Batch**: home
- **Depends**: 0356, 0384
- **Files**: `src/media_hygiene/review/http.py`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/services/launcher_lan.py`, `src/media_hygiene/review/lan*.py`, `src/media_hygiene/search/app.py`, `tests/unit/test_home_lan.py`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

## Context

Maintainer, 2026-10-24: search and browse on the phone are welcome ("it is not a problem"). What
must hold: only a **paired** device of the home Wi-Fi reaches them, never a guest, a TV or a
connected object of the same network. Today `mh --lan` pairs a phone by a QR code or an 8-digit
code (0269) and serves the home page only; search and browse accept the PC alone (loopback `Host`
check, `review/http.py` `is_local`).

## What to do

1. One check for every route of the home server: the PC itself, or a paired device (the cookie of
   0269); everything else 403 — the pages served by 0356/0357 included, their thumbnails and
   files too.
2. Which pages a phone may open: an explicit list (search, browse, albums, slideshow's remote),
   the others refused with *open it on the PC*. Steps stay refused from the phone (0269:
   *Run this step on the PC*); a page that writes (0361) is decided page by page.
3. Tests: a paired phone opens search and a thumbnail; an unpaired one gets 403 on every route
   (a test walks the route table: none forgotten); the PC unchanged.
4. Docs en + fr: what a paired phone can open.

## Acceptance

- From a paired phone: search, browse, a photo opened; from an unpaired device of the same
  Wi-Fi: nothing, on any path.

## Gain

Search and browse from the sofa, safely.
