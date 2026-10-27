# 0384 — `mh --lan`: a forged `Host` header passes for the PC itself

- **Priority**: High — security: any device of the home network may get the PC's rights under `mh --lan`
- **Batch**: home
- **Depends**: —
- **Files**: `src/media_hygiene/review/http.py`, `src/media_hygiene/review/serving.py`, `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/lan.py`, `src/media_hygiene/services/launcher_lan.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `tests/unit/test_home_lan.py`, `tests/integration/test_album_phone.py`, `tests/measure/mh-measure.ps1`
- **Measure (after)**: a step of `tests/measure/mh-measure.ps1` written by the implementation (the forged `Host` refused on Windows + Docker Desktop), run by the maintainer afterwards (decided 2026-10-27)

## Context

Found on 2026-10-25 while fixing the search's thumbnails (404 under the home server: `AlbumPages`
answered every `/thumb/`). Every server decides that a request comes from the PC by its `Host`
header only: `review/http.py` `is_local` (loopback name or address, any port), used in 12 modules.
`Host` is written by the client. Under `mh --lan` the port is also published on the PC's address
on the home network (`services/launcher_lan.py`), and `LanApp.handle` passes on as the PC's any
request where `is_local(request)` is true, **before** looking at pairing:

```python
if is_local(request) or not self.lan.names_me(request):
    return await self.home.handle(request)
```

So a device of the same Wi-Fi (a guest, a TV, a connected object: exactly who 0360 wants kept out)
that sends `GET /search` to `192.168.x.y:8088` with `Host: 127.0.0.1:8088` would bypass pairing:
search, originals, the steps of the home page (an audit, *Apply now* — what moves files to the
quarantine), the quit. Not tested on the real setup yet (**to check**): read in the code only;
no browser sends such a header, a script does (`curl -H`).

Inside the container, the peer address does not tell the PC from a phone either: Docker
Desktop's port forwarding probably makes every connection arrive from the same internal address
(**to check**, `writer.get_extra_info("peername")` logged under `mh --lan`).

## What to do

1. Confirm the hole (maintainer, a step of `tests/measure/mh-measure.ps1`, run during `mh --lan`):
   from the PC itself, `Invoke-WebRequest -Uri http://<lan address>:<port>/api/state -Headers
   @{Host='127.0.0.1:<port>'}` — 200 means the hole is real (to check whether PowerShell 5.1
   lets `Host` be set; else `curl.exe -H`). Log the peer address seen in the container too.
2. Tell the doors apart by the socket, not by a header: the container listens on two ports, the
   loopback publish on the usual one (`-p 127.0.0.1:8088:8088`), the home network publish on
   another container port (`-p <lan address>:8088:<lan port>`); the server reads the local port of
   the connection (`writer.get_extra_info("sockname")`) and attaches it to the `Request`
   (e.g. `Request.door: Door.PC | Door.LAN`). `is_local` becomes "came in through the PC's door
   **and** names a loopback host" (the `Host` check stays: DNS rebinding).
3. `LanApp`: a request of the LAN door is never handed on as the PC's, whatever its `Host`; only
   the pairing paths and, once paired, the phone's reads/writes (0269, 0297). The header
   `x-media-hygiene-phone` added on 2026-10-25 (`share/album_page.py` `PHONE_HEADER`) can then
   be replaced by the door.
4. The same for `mh slideshow --lan` (0291) and any other server published with `--lan`.
5. Tests: a request of the LAN door with `Host: 127.0.0.1` gets the pairing page / 403 on every
   route of the home server (a test walking the route table); the PC unchanged; a paired phone
   unchanged.

## Acceptance

- The check of step 1 answers 401/403 after the fix (measured on Windows), 200 before.
- No route of a server started with `--lan` trusts `Host` alone.

## Gain

`mh --lan` stops handing the PC's rights — up to moving files to the quarantine — to any device of
the home network. 0360 (every page behind pairing) relies on this check: do 0384 first.
