# 0675 — Large view preloads the next and previous photo

- **Priority**: Low
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/pick_viewer.js.j2`, `src/media_hygiene/search/templates/search_events_ahead.js.j2`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

In the large view, → asks for `/preview/<key>.jpg` only when pressed. *Measured*
(devcontainer, 2026-11-10): rendering the 1600 px preview of a 12 MP JPEG takes 74 ms (best
of 5, file in the page cache; 327 KB sent), more with the read of the original on a Windows
share. `pick_viewer.js.j2` holds no `new Image()` preload; only the Events review loads
ahead (`search_events_ahead.js.j2`, 0652).

## Proposal

- When a photo is shown, the shared viewer loads the next one in the direction of travel
  and the previous one (`new Image().src`), cancelled when the user jumps; never a video.
- One preload at a time, so a fast run of → never queues more than one render.
- Shared: every page with the large view gets it; the Events review uses the same code.

## Acceptance

- [ ] Headless Chromium, mocked API with a 300 ms preview: the second → shows its photo
      without waiting; no more than 2 preview requests in flight
- [ ] No preload on a phone using mobile data saver (`navigator.connection.saveData`)

## Where the user gains

Each → in a review: about 75 ms + the read (measured / to measure on Windows) → instant
from the second photo on.

## Status — PARTIAL (2026-11-11)

### Done

- `pick_preload.js.j2` (included by `pick_viewer.js.j2`, so every page with the large view):
  the next photo in the direction of travel, then the previous one, `new Image().src`, one
  at a time; dropped and stopped on a jump or on close; never a video; none when
  `navigator.connection.saveData`.
- Rendered-page test (`test_pick_pages`) and the CI browser walk `tests/support/preload_walk.py`
  (300 ms previews, second -> without waiting, at most 2 previews in flight) called from
  `tests/e2e/test_ask_dialog_browser.py`.

### Not done

- The browser walk has not run (no Playwright here): CI to confirm.
- The Events review's own code (`search_events_ahead.js.j2`) is kept: it preloads the next
  *event's* 60 thumbnails (a different job from the viewer's neighbours); the Events tab
  already uses the shared large view, so it gets the new preload.
