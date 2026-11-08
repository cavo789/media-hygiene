# 0659 — Slideshow on this PC: the screen in a full-screen tab, paired at once, the keyboard as remote

- **Priority**: Medium
- **Batch**: tv-slideshow
- **Depends**: —
- **Files**: `src/media_hygiene/slideshow/templates/`, `src/media_hygiene/slideshow/screens.py`, `src/media_hygiene/slideshow/tv_door.py`, `src/media_hygiene/slideshow/routes.py`, `documentation/en/commands/slideshow.md`, `documentation/fr/commands/slideshow.md`

## Problem

A show can only be watched on a TV (or by the hidden *Plan B*: open `/screen` on the PC, type the
pairing code, drive it from another window). Without a TV (office, travel, a laptop) there is no
slideshow, although the screen is a plain web page the PC's own browser could show. Asked by the
maintainer on 2026-11-08.

## Decided (2026-11-08, maintainer)

- The screen opens in a **new tab, full screen**, with **no code**: a screen opened from the PC
  itself (loopback, and Docker Desktop's gateway as the other local pages recognise it) is paired
  at once. A screen from the home network still asks its code, as today.
- **The keyboard is the remote**: ← → previous / next, Space pause / play, Esc leaves full
  screen, S stops the show. A small bar (the same buttons, a ✕) shows when the mouse moves and
  hides after a few seconds still.
- Everything else unchanged: same show, title cards (0654), videos; a paired phone still drives it.

## Fix

1. Screen page: keyboard handler and the auto-hiding bar (in its own include, templates are
   shared with the TV's screen: the TV's remote keys OK/arrows keep working as today).
2. Server: loopback screen paired without a code (a test: a LAN address still gets the code).
3. An entry point the next TODO (0660, the ▶ *Slideshow* menu) calls: start the selection, then
   open `/screen?here=1` in a new tab; full screen asked on the user's click (browsers refuse it
   otherwise).
4. Docs en/fr: *Plan B* becomes the PC section ("No TV: on this PC"); the keys listed.

## Acceptance

- [ ] A screen opened from the PC shows the show without a code; from the LAN, the code (tests)
- [ ] ← → Space Esc S do what they say; the bar hides after the mouse stops (headless Chromium)
- [ ] The TV's screen behaves as before (its tests unchanged)
- [ ] Docs en/fr; `docs_screenshots` flagged stale
