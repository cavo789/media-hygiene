# 0518 — Every action on picked files ignores the files set aside

- **Priority**: high
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/share/album_pickers.py, src/media_hygiene/share/album_api.py, src/media_hygiene/search/move_go.py, src/media_hygiene/search/rule_go.py, src/media_hygiene/search/events_choose.py, src/media_hygiene/search/chosen_api.py, src/media_hygiene/review/templates/pick_grid.js.j2, src/media_hygiene/search/templates/search_events.js.j2, src/media_hygiene/search/templates/search_rule.js.j2

## Context

In `mh search` / `mh browse`, a file set aside (in the decisions file, not yet removed by
*Apply now* / `clean --decisions`) stays shown in the grid with its label, so Ctrl+A,
Shift+click, the rectangle or *every file found* (`all`) pick it too. Every action then takes it:
read in the code (2026-10-30, not tried in the app), nothing filters the set-aside files in
`share/album_pickers.py` (album, so also the share/zip built from it), `search/move_go.py`
(event move), and the other key-based posts (period rule `rule_go`, events `events_choose`,
📺 *On the TV* slideshow). `share/album_api.py`'s docstring claims "the files set aside never
enter an album": false today. An event move even moves a photo the user meant to discard.

The maintainer's rule: once set aside, a file is treated **as if it no longer existed** by every
following action on a picking, whatever the gesture that picked it.

## Acceptance

- [ ] Inventory every endpoint/page action that takes picked keys or `all` (album add, share,
      event move + its preview, period rule trial/go, events sort choices, TV slideshow, any
      other found while doing it, on every page built on `pick_*`) — listed in the commit.
- [ ] Each one drops the files set aside **server-side** (one shared helper reading the
      decisions file, so a stale page cannot bypass it), for keys and for `all`.
- [ ] The answer says how many were left out ("3 files set aside ignored"), shown in the bar.
- [ ] *Set aside* / *Take back* themselves keep working on set-aside files (the only exception).
- [ ] Counts in the bar ("N picked") either exclude set-aside files or say so — decide.
- [ ] One test per action: a picking holding a set-aside file → the action does not touch it.
- [ ] `album_api.py` docstring true again; docs (en + fr) say set-aside files are ignored by
      the actions; `i18n_update` + French translation.
- [ ] Related: 0517 (large view arrows skip set-aside files) — same "as if gone" rule.
