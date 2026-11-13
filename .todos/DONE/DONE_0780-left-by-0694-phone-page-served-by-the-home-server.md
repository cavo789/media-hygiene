# 0780 — What 0694 left: The phone page served by the home server, so it gains ▶ Slideshow to the TV

- **Priority**: Medium
- **Batch**: phone
- **Depends**: —
- **Files**: `.todos/PARTIAL/PARTIAL_0694-phone-page-served-by-the-home-server.md`, `src/media_hygiene/services/phone_review.py`, `src/media_hygiene/cli/cmd_phone_review.py`, `src/media_hygiene/services/launcher_phone_free.py`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/share/album_route.py`

Split from section 0694 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/PARTIAL/PARTIAL_0694-phone-page-served-by-the-home-server.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The phone page is answered by the home server; no second server is started
- ▶ Slideshow ▾ › On the TV starts the chosen tiles on `/screen` (test)
- The way back home and *Apply now* are there, as on every set-aside page

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — DONE (2026-11-13)

Already done by 0694 and only unticked in its acceptance list (its own Status says so):
`/phone/` served by the home server (`services/phone_here.py`, `phone_here_parts.py`, in
`pages_here`), no second container; ▶ Slideshow ▾ › On the TV through the home server's
`TvSlot`; ⌂ home and *Apply now*. Checked: `tests/unit/test_phone_here.py` (7 passed,
2026-11-13), among them `test_on_the_tv_shows_the_tiles_chosen` and
`test_served_with_the_slideshow_the_way_home_and_apply`. Left for the maintainer as before: a
real try with a phone on Windows; captures tracked in 0717.
