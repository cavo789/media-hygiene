# 0269 — Open the home page from a smartphone on the home network

- **Priority**: Low — an idea for later, asked by the maintainer (2026-10-20)
- **Batch**: home
- **Depends**: 0266
- **Files**: `src/media_hygiene/review/http.py`, `src/media_hygiene/review/local_app.py`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/services/launcher.py`

## Context

The maintainer would like to open the Media Hygiene menu from a smartphone (2026-10-20): the
tool running on the home PC, or one day on a NAS. 0266 makes the page usable at phone width.
Reaching it from another device is a different matter, deliberately closed today:

- `review/http.py` answers only a request naming a loopback host (`localhost`, `127.0.0.1`,
  `[::1]`);
- `mh` publishes the page's port on `127.0.0.1` only (`-p 127.0.0.1:<port>:<port>`);
- a step chosen on the page runs in the PowerShell window, which asks its questions there
  (`clean` confirms, `purge` confirms). From a phone, nobody sees that window.

On the NAS itself: the image is built for amd64 and arm64. Whether the maintainer's DS216j can
run containers was not confirmed on 2026-10-20: Synology's Container Manager page lists no
models. To check in the NAS's Package Center.

## Decisions for the maintainer

1. **Who may open it.** A pairing code or a QR code shown on the PC, a token kept in a cookie,
   and the LAN only, never the internet. What is lost: today nothing on the network can reach
   the page; afterwards, anyone on the Wi-Fi who has the code can.
2. **HTTP or HTTPS on the LAN.** Plain HTTP is simple, but the token travels in clear on the
   Wi-Fi. A self-signed certificate makes phones warn. To weigh.
3. **The questions asked in PowerShell.** Every step started from the phone must ask in the
   page (a confirmation dialog, then the progress), as the audit run by the page already does
   (0211). That is a change for each acting command (`clean`, `undo`, `purge`, `sort`,
   `import`…): one step at a time, and maybe only the read-only ones (🔒) at first.

## What to do (once decided)

- A setting or a `mh` option that opens the page to the LAN for this run only, said in one line
  with the address and the code.
- The Host check accepting the PC's LAN address once paired.
- The steps the phone may run, listed, each with its questions moved into the page.

## Acceptance

To write once the decisions are taken. The maintainer's phone opens the page over the Wi-Fi
with the code, and runs at least `audit` from it.

## Decided (2026-10-21)

By the maintainer (`/todo:inbox`):

1. **Access**: a pairing code (and its QR code) shown on the PC, a token kept in a cookie, the
   LAN only, opened by an option for this run only, never the internet.
2. **Plain HTTP** on the home network (no self-signed certificate warnings); the session is short.
3. **Read-only steps (🔒) first**: the phone runs only them; acting commands stay on the PC
   (moving their questions into the page is a later TODO).

The test from the maintainer's phone on the home Wi-Fi (Windows firewall prompt included) comes
after the implementation: an unattended run closes PARTIAL on it.

## Status — PARTIAL (2026-10-21)

### Done
- `mh --lan` (Windows PowerShell, `mh_lan.ps1.j2`): the home page loop of `mh` alone, its port
  also published on the PC's private IPv4 address (the adapter with a default gateway;
  `10/8`, `172.16/12`, `192.168/16` only; never `0.0.0.0`), for `home` only, for this run only;
  a 32-byte secret drawn with `RandomNumberGenerator` (no `Add-Type`), kept for the whole loop
  so a phone stays paired across the steps; says the address, the firewall prompt to expect,
  and a network Windows counts as Public. The bash `mh` refuses it (PowerShell only).
- `review/lan.py` + `review/lan_app.py`: in front of the home page, the loopback unchanged;
  `Host` must be exactly `<address>:<port>`; an 8-digit code and the cookie token both derived
  (HMAC) from the secret; `/pair/<code>` sets an HttpOnly SameSite=Lax cookie, 5 wrong codes
  close the pairing until the server stops; a paired phone may only read (page, state, audit
  progress, reports, assets, docs) and run the page's audit (`POST /api/audit`, Origin
  checked); a step, Quit and the presence stay the PC's (403, "Run this step on the PC").
  `GET /api/lan` (loopback only) gives the PC's page the address, the code and a QR code
  (segno, a new dependency: pure Python, BSD, 292 KB installed, measured).
- The phone's page (`remote`): no Quit, no presence, each step's button says to run it on the
  PC. The PC's page: an "On your phone" card in the sidebar (QR, address, code).
- Docs en+fr (`commands/home.md`, `commands/launcher.md`), translations, tests
  (`tests/unit/test_home_lan.py`), step 29 of `tests/measure/mh-measure.ps1`.

### Not done
- The test from the maintainer's phone on the home Wi-Fi: Windows' firewall prompt for Docker
  Desktop, whether Docker Desktop publishes on the PC's LAN address as asked (`-p
  <address>:8088:8088`), the QR code read by the phone's camera, the audit run from the phone,
  the page unreachable from mobile data.
  **Reason:** needs the maintainer's PC and phone: `mh-measure.ps1 -Only 29 -Count 20`.
- Moving the questions of the acting commands (`clean`, `undo`, `purge`, `sort`, `import`)
  into the page, so that a phone may run them.
  **Reason:** decided later (decision 3, 2026-10-21): read-only steps first; a TODO of its own.
- `mh --lan` from bash (WSL, Linux, macOS).
  **Reason:** Docker under WSL publishes on Windows' loopback; Windows-first; no request yet.
