# 0334 — One album opened by a link on someone else's phone, without pairing

- **Priority**: Low
- **Batch**: share
- **Depends**: 0297
- **Needs maintainer**: the design: how the link is made and given (QR code, mail), how long it lasts, what it lets the phone see (one album only), whether the PC must stay on
- **Files**: `src/media_hygiene/share/album_page.py`, `src/media_hygiene/share/templates/album.html.j2`, `src/media_hygiene/review/lan_app.py`, `documentation/en/`, `documentation/fr/`

## Why

The maintainer, 2026-10-22 (recorded in 0293), then 2026-10-23 at the start of `/todo:iterate`:
0297 shows the albums on a phone **paired** with the PC (`mh --lan` and its code); a relative's
phone should open **one album** from a link, without being paired and without seeing anything
else. Split from 0293, which is now the home page of a paired phone.

## What

To design first (a short note in `.claude/plans/`, then the maintainer's review): the link's
secret (a random token per album, revocable), its lifetime, the refusals (any other path, any
other album), the PC that must be on and on the home network (this is not a public share), the
album page of 0297 reused read-only.

## Tests

To write with the design.
