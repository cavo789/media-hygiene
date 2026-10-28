# 0445 — Maintainer checks after the phone work of 2026-10-27/28

- **Priority**: High
- **Batch**: phone
- **Depends**: —
- **Files**: `tests/measure/mh-measure.ps1`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`
- **Needs maintainer**: every check below runs on the maintainer's PC and phone

## Why

The sessions of 2026-10-27/28 changed the phone side a lot (HTTPS, durable pairing, installable
app, read-only phone, review keys). Tests pass in CI, but nothing was tried on the real devices
after the last fixes. This TODO is the list to pick up at the next session: answer each line,
then close it or file a TODO for what fails.

## To do, in order

1. Merge pull request #46 (salvage of `measure-29-lan`, 0443, 0435), wait for the image.
2. On the PC: `mh update`, then `mh config --upgrade` (adds `[review] lan = true` and the other
   new settings, keeps yours).
3. Phone, pairing: pair once more (the cookie is `SameSite=Lax` now), close the app, open it
   from its icon: **no code asked**? The PC's card lists the phone under *Phones paired for good*?
4. Phone, search (0443): the tiles show their previews (no more *No preview*)?
5. Phone, large view: a swipe goes to the next / previous photo?
6. Phone, read-only: no album bar, no keyboard panel, no tick boxes, no *Excel* nor PC actions in
   *Find* and in *What do you want to do?*; the album page shows no ➖ ➕ 🖼?
7. Phone, back to home: how long does the splash stay (seconds)? Feeds 0442.
8. `mh import --phone`, then `mh import --phone --free`, phone plugged in (0379).
9. `.\mh-measure.ps1 -Only 29 -Count 1` (step 29 reworked: family view, write buttons, HTTPS).
10. `docs_screenshots` (and `docs_screenshots fr`): many pages and console outputs changed.

## Explicit NON-goals

- New features: each failure becomes its own TODO.
