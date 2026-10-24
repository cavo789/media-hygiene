# 0331 — Freeing a phone: a tick is refused with "Not saved (error 405)"

- **Priority**: High
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/review/presence.py`, `src/media_hygiene/review/templates/home_link.html.j2`, `src/media_hygiene/review/phone_app.py`, `src/media_hygiene/review/decide_route.py`, `src/media_hygiene/review/ending.py`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/services/phone_review.py`, `src/media_hygiene/review/templates/phone_review.js.j2`, `src/media_hygiene/review/templates/phone_review.html.j2`, `tests/integration/test_phone_review.py`

## Why

The maintainer, 2026-10-23, testing the new page of `mh phone --free` (0312/0314, commit
e40ab92) on their phone "A72": the page loads (743 files ticked, 3.1 GB, folders *Camera*,
*Facebook*, *Maison*…), but a choice answers **"Non enregistré (erreur 405)"**; the browser's
console: `POST http://127.0.0.1:8088/api/phone 405 (Method Not Allowed)`. Nothing can be
unticked: the page is unusable, and the red button would delete every file ticked by default.

The maintainer's answer, 2026-10-23: opened from the desktop shortcut → home page → *Make room
on the phone* (the home page's step, not `mh phone --free` typed in the console).

## Leading hypothesis (read in the code, 2026-10-23, not reproduced)

The phone page is the only page served with a `Presence` (`EndingDoor(app, app.ending,
Presence(app.ending, STOPPED))` in `services/phone_review.py`) that **never says it is alive**:
it does not include `home_link.html.j2`, which sends `POST /api/alive` every 10 s and on
`pagehide` (0262). `Presence` waits for a first tab to speak, then ends the server after
`SILENCE_SECONDS` (180 s) without news, or `LEAVING_GRACE_SECONDS` (10 s) after a tab left.
Opened from the home page, the home page's tab keeps pinging `/api/alive` on port 8088 while
the step runs, and sends `leaving` when it reloads: the phone server takes that tab as its
own, then hears nothing from the phone page → it ends itself as *Leave everything* (nothing
deleted), `mh` brings the home page back on 8088, and the phone page's next `POST /api/phone`
reaches `HomeApp`, which answers 405 to a POST it does not know (`home_app.py`).

To confirm: the console's lines at the moment (did `mh` say the page ended, nothing deleted?);
in a test, a `serve_phone_review` with a `POST /api/alive` `{"leaving": true}` then no news:
the server ends after the grace.

The fix is shared with 0332 (the phone page includes `home_link.html.j2`: its pings, its way
back); keep here the test through the real server and the plain message.

## What else is known

- Every page of the tool listens on the same port, 8088 (`config/review_settings.py`,
  `PAGE_PORT`).
- `PhoneApp` (`phone_app.py`) answers `POST /api/phone` through `DecidingApp.answer`
  (`decide_route.py`): 405 only for a path or a method it does not know. The integration tests
  post `/api/phone` to `PhoneApp` directly (`serve_app_and_call`) and pass; **no test posts it
  through the real server** (`serve_phone_review` → `EndingDoor.handle` → `asset_or_page`):
  `_serve` in `test_phone_review.py` only sends `GET /`, `/api/free` and `/api/stop`.
- The home page's server (`home_app.py`) answers 405 to any `POST` it does not know, so
  `/api/phone` too.

## Hypotheses to check, in this order

1. **Another server answers on 8088** (the leading hypothesis above): the phone page's tab outlived its server (the home page
   came back on the same port, or a second `mh` run), so its `POST` reaches `HomeApp`. Check:
   `GET /api/state` from the same tab at the moment of the error; what `mh` printed. If so: the
   page must notice its server is gone (as `home_link.html.j2` does) instead of saying "error 405".
2. **The real door routes `POST /api/phone` wrongly**: write the missing test first
   (`serve_phone_review` in a thread, `POST /api/phone`, the file read back); it tells at once.
3. **The page posts to the wrong path or method**: `phone_review.js.j2` sends `DECIDE_PATH`
   through `ask()` of `pick_grid.js.j2`; check the rendered `decide_path` and the request in the
   browser's Network tab (method, path, `Content-Type`).

## Done when

- The cause is named; the fix carries a test through the real server (`serve_phone_review`).
- A choice whose server is gone says so plainly ("The page is not running any more: type mh
  phone again"), never a bare status code — and the red button is refused while the ticks
  shown are not those read back from the disk.

## Docs

None unless the behaviour visible to the user changes.
