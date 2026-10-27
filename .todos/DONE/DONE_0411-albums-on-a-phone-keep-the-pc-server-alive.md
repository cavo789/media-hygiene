# 0411 — Albums open on a paired phone keep the PC's home server alive

- **Priority**: Low
- **Batch**: share
- **Depends**: —
- **Files**: `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/templates/presence.html.j2`, `src/media_hygiene/share/templates/album.html.j2`, `tests/integration/test_album_phone.py`

## Context

0341 (commit 363c452, PARTIAL) made the albums page ping `/api/alive`, so the home server stays
up while the albums are shown on the PC. On a phone paired with `mh --lan`, `lan_app` refuses
that ping: the PC's server may stop while the phone still shows the albums, and no "stopped"
overlay shows on the phone. Maintainer, review of 2026-10-27: a paired phone keeps it alive too.

## Steps

1. `lan_app` lets a paired phone's `GET /api/alive` through (cookie checked as for any page).
2. The overlay of `presence.html.j2` shows on the phone when the PC's server is gone.
3. Test: a paired phone's ping keeps presence alive; an unpaired one is still refused.

## Acceptance

- Albums open on a paired phone: the PC's home server does not stop while they are shown.
- An unpaired device's ping is refused as before.
