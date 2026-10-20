# 0261 — Pages: a Quit button, and the page stops by itself once no tab shows it

- **Priority**: Medium
- **Batch**: launcher
- **Depends**: —
- **Files**: `src/media_hygiene/review/ending.py`, `src/media_hygiene/review/templates/home.html.j2`, `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/review/templates/home_link.html.j2`, `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh.sh.j2`, `documentation/en/commands/home.md`, `documentation/fr/commands/home.md`

Seen in the maintainer's step 14 run (2026-10-20, 0210): they "quit" the home page by
closing its browser tab with its X, as anyone would. The page kept running in the PowerShell
window (port 8088 held, no prompt) until Ctrl+C. Decided by the maintainer (inbox 2026-10-20):
**both** a Quit button and an automatic stop once no tab shows the page.

## Today

- A page's server ends on Ctrl+C, on `POST /api/stop` (the "⌂ Home" link of every page but home:
  exit code 0, `mh` opens home again), or on a step chosen at home (`100 + n`) (`review/ending.py`).
- `mh` alone loops on the home page; exit code 0 from home (Ctrl+C) ends the loop and gives the
  prompt back (`mh_menu.ps1.j2`, `_mh_home`; `mh.sh.j2` the same).
- The home page shows "Stop this page with Ctrl+C in the window where mh runs" (`home.html.j2`).

## To do

1. **Quit button** on the home page (next to the title, or at the bottom with that line): `POST
   /api/stop` on home → exit 0 → the loop of `mh` ends, the prompt comes back. The page then
   shows a closing line ("Media Hygiene is stopped: you can close this tab.") rather than an
   error once the server is gone. The Ctrl+C line stays, shorter.
2. **Stop once no tab shows it**: the page tells the server it is alive (a light request every
   few seconds while open), and on `pagehide` (`navigator.sendBeacon`, *to check*: a beacon's
   content type against the JSON-only POST rule of these servers). The server ends after a
   grace delay without news — long enough that a reload, or a step run that reloads the page,
   never stops it (proposed 15 s; *to check*: browsers throttle the timers of hidden tabs, up to
   once a minute in Chrome after a while, so a tab left in the background must not count as
   closed — prefer the beacon as the signal and the silence only as a long fallback, e.g. 2 min).
   Say in the console, one line, why it stopped ("The page's tab was closed: Media Hygiene
   stopped.").
3. **Other pages** (`review`, `review-sort`, `people`, `places`, `search`, `phone`…): the same
   stop on tab closed, but **not** exit 0 — today 0 makes `mh` open home again, which would
   reopen a tab the user just closed. A distinct exit code ("closed by the user") that ends
   the `mh` loop, in `mh.ps1` and `mh.sh` alike. Decide while implementing whether pages other
   than home get it in this TODO or a follow-up (they share `ending.py`).
4. Never while a step runs from the page: the home server already ends when a step is chosen;
   the audit run *inside* the page (0211) must not be cut by the grace delay (the page polls
   it, so it is alive) — test it.
5. Tests: the beacon ends the server with the right code; a reload within the grace delay does
   not; silence beyond the fallback does; the loop of `mh` ends on that code (rendered script
   tests). Docs en + fr (`commands/home.md`, the line about Ctrl+C); `docs_screenshots` (the
   home page changes): to run later, say it.

## Settings?

The grace delays are UI timings, not machine-dependent: constants (same reasoning as the 30 s
hint of 0258, kept a constant by the maintainer on 2026-10-20).

## Gain

Estimated: closing the tab — the gesture the maintainer used — frees the port and gives the
PowerShell prompt back; before, a hidden `Ctrl+C` step that the page states only in a muted line.
