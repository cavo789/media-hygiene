# 0462 — One album by a 24 h link on someone else's phone: the implementation (rest of 0334)

- **Priority**: Low
- **Batch**: share
- **Depends**: 0384
- **Files**: `src/media_hygiene/share/album_page.py`, `src/media_hygiene/share/templates/album.html.j2`, `src/media_hygiene/review/lan.py`, `documentation/en/`, `documentation/fr/`

## Why

0334 (closed) finished and got the design approved (`.claude/plans/0334-album-link-design.md`,
private): the code is left.

## What (decided 2026-10-27)

In-memory random token per album (192 bits, `compare_digest`, 24 h, dropped by *Stop sharing* or
a restart of `mh`); routes `/a/<token>` on the LAN door only, before the pairing check; read-only
album page, photos and videos of that album alone; `POST /api/album-link` loopback-only; QR code
plus a link to copy.

## Acceptance

The tests listed in the design note (other path, other album, expired or revoked token, forged
`Host`); docs en + fr.
