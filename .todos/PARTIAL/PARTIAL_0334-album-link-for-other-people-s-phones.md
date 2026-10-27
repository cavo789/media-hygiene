# 0334 — One album opened by a link on someone else's phone, without pairing

- **Priority**: Low
- **Batch**: share
- **Depends**: 0297, 0384
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

## Decided (inbox, 2026-10-27)

The maintainer chose: a QR code shown on the PC plus a link to copy (to send by mail or
message); the link lasts **24 h**; it shows **one album, read-only** (no set-aside, no other
album, no search); the PC stays on with `mh --lan` (no cloud, nothing leaves the home network).
Depends on 0384: no link before the forged `Host` hole is closed.

## Status — PARTIAL (2026-10-27)

### Done
- The design note (private, `.claude/plans/0334-album-link-design.md`): an in-memory random
  token per album (192 bits, `compare_digest`, 24 h, dropped by *Stop sharing* or a restart),
  routes `/a/<token>` on the LAN door only, before the pairing check, read-only album page,
  pictures of that album's keys alone, the PC's `POST /api/album-link` loopback-only, the QR code
  as `lan_response`, and the tests to write.

### Not done
- The implementation and its tests.
  **Reason:** a security feature (a door without pairing) — the two open points of the note
  (tokens lost at a restart of `mh`, or kept in `/reports`; videos over the link or photos only)
  change what is built; to confirm before writing it, as the TODO asked ("the maintainer's review").

## Decided (2026-10-27)

By the maintainer, on the design note's two open points:
- Link tokens stay **in memory** only: a restart of `mh` revokes every link (nothing secret on
  disk).
- **Photos and videos** go over the link (videos play in place, as on a paired phone).
The design is now complete: the code can be written.
