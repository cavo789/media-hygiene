# 0829 — 🖥 Slideshow *On this PC*: "Avoid some people" before it starts

- **Priority**: High
- **Batch**: tv-slideshow
- **Depends**: none
- **Files**: `src/media_hygiene/slideshow/templates/screen_here.html.j2`, `src/media_hygiene/slideshow/templates/screen_here.js.j2`, `src/media_hygiene/slideshow/templates/slideshow_avoid.js.j2`, `src/media_hygiene/slideshow/avoid_desk.py`, `src/media_hygiene/services/slideshow_selection.py`, `src/media_hygiene/review/templates/slideshow_menu.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Reported (maintainer, 2026-11-15)

`/library`, 2026 (344 photos), ▶ Slideshow ▾ → 🖥 *On this PC*: the show opens straight
on the full-screen tab (`/slideshow/screen?here=1`, 0659, `HERE_SCREEN` in
`slideshow_selection.py`), whose only controls are the keyboard bar of
`screen_here.*`. No remote → no *Avoid some people* (0825 put it on the remote,
`/slideshow`). 📺 *On the TV* has it.

## What

Every entry that starts a show offers the filter (rule of workflow.md, memory
`feature-follows-its-kind`). List them first and check each: library ▶ (PC, TV), album
▶, home TV choices, `/person`/`/people` if they start shows.

- *On this PC*: before the first photo, the same block as the remote (people seen on the
  show, `✓ n · ≈ n`, from `GET /api/avoid`; `POST /api/avoid`), then *Start*. Nobody
  seen → starts at once, as today. Also reachable during the show from the bar
  (a key, listed in its keys line), pausing it.
- **One component**: the block's script is `slideshow_avoid.js.j2`, shared by the remote and
  the screen bar (no copy). Caution: `screen.html.j2` is the TV's page, **ES5 only, no
  regex** (`tests/support/es5.py`); `screen_here` runs only on the PC's own tab but is
  included in it — check whether the shared script must be ES5 too, or load it only with
  `here=1`.
- Nothing stored, as on the remote.

## Tests

- *On this PC* with a named person on the selection: the block shows before the first
  photo; ticking sets their photos out (`show.skipped`).
- Nobody seen: no block, the show starts at once.
- ES5 check still passes on the TV's page.
