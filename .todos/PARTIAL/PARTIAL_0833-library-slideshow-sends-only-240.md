# 0833 — Library ▶ Slideshow: 344 found, only the 240 shown reach the show

- **Priority**: High
- **Batch**: tv-slideshow
- **Depends**: none
- **Files**: `src/media_hygiene/review/templates/pick_grid.js.j2`, `src/media_hygiene/review/templates/pick_slideshow.js.j2`, `src/media_hygiene/share/album_pickers.py`, `src/media_hygiene/share/album_api.py`, `src/media_hygiene/services/slideshow_selection.py`, `src/media_hygiene/search/views.py`

## Reported (maintainer, 2026-11-15)

`/library`, 2026-01-01 → 2026-12-31: "344 fichiers trouvés ; les 240 premiers sont
affichés". Nothing picked, ▶ Slideshow ▾ → 📺 *On the TV*: the remote says "Photo 17 sur
**240**". 240 = `FIRST_HITS` (`search/views.py`): the show got the files loaded, not the
344 found.

## What is known (read, not run)

- `toTv` (`pick_grid.js.j2:320`) sends, nothing picked, `{keys: <the files loaded>, all:
  total > files.length, search: scope()}`; `FoundPicker.files` (`share/album_pickers.py`)
  reads the whole search when `all` is true. So either `total` is not 344 there, `all`
  is lost on the way, the library's TV route does not use `FoundPicker`, or the slideshow
  side caps it. Reproduce on the demo tree with more than 240 files before fixing.
- The menu's count (`pick_slideshow.js.j2`, `shown()`) states `total`: check that the count
  the button said ("· 344 photos") is the count shown — product rule: an action acts on
  what it states.
- Videos and files set aside are left out of a show: if that is the difference, the remote
  must say it ("344 found: 240 photos shown, 104 videos/set aside left out").

## Tests

- A search of 300 files, nothing picked, ▶ On the TV: the show holds every showable file,
  and the button's count equals the show's total (or the difference is said).
- Same for 🖥 On this PC and for *everything* picked (Ctrl+A).

## Status — PARTIAL (2026-11-15)

### Done
- Server side checked: 344 dated files, the page's body (`all: true`, 2026 dates) →
  `SearchPicker` returns 344; a send of 300 found / 240 shown starts a show of 300
  (`tests/unit/test_tv_all_found.py`).
- Real bug fixed: Ctrl+A or *Invert* picks the 240 shown (`everything` false) → only those
  240 were sent. New `showing()` in `pick_grid.js.j2`: nothing picked or every shown file
  picked on a partial search = every file found (`all`, counted as `total`); the menu's
  count (`pick_slideshow.js.j2`) and `toTv` use it, so the count stated is what is sent.
- Other entry points checked (albums, album edit, /person, phone, events span 📺, random /
  folder / period choices): none shows fewer files than found.

### Not done
- The exact report (nothing picked → 240) not reproduced: needs the maintainer's answer
  (was anything picked?) or a DevTools capture of the `POST /api/albums` body.
  **Reason:** the server and the client code for "nothing picked" both behave.
- The remote does not say when the show holds fewer files than sent (videos, sidecars,
  files not indexed). **Reason:** `services/slideshow_here.py` is at the 200-line cap and
  `begin` returns a bool: needs its own split.
