# 0430 — HTTPS on the home network: a local CA, its download page, the `/lan` folder

- **Priority**: Medium
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/review/lan.py` (200/200: new code in new modules, e.g. `review/lan_tls.py`, `review/lan_ca_page.py`), `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/listen.py`, `src/media_hygiene/review/doors.py`, `src/media_hygiene/paths/` (`mounts.py` 194/200), `src/media_hygiene/services/launcher_lan.py`, the `mh` launcher template (`mh_lan.ps1.j2`), `documentation/en/`, `documentation/fr/`
- **Needs maintainer**: a test on the maintainer's Android phone and on an iPhone (later: the "to check" points below)

## Split (2026-10-27)

Too large for one run: this TODO keeps design points 1–3 and the `/lan` folder (the
foundation). Point 4 (durable pairing) is TODO 0431; points 5–7 (manifest, service
worker, offline page, shared splash) are TODO 0432. The whole design stays below for context.

**Library decided (measured 2026-10-27):** the `openssl` CLI, already in `python:3.14-slim`
(`which openssl` in the base image; the `runtime` stage removes nothing), called as a
subprocess like `ffprobe`: +0 bytes. `cryptography` would add 16 MB installed (measured,
`uv pip install --target`, Python 3.14).

## Goal

From home, the maintainer scans the QR code of `mh` once and the phone offers to install
"media-hygiene" as an app. Afterwards the icon opens the home page directly, without a QR code
or a code, and when `mh` is not running on the PC it shows a clean page instead of the
browser's error. Nothing is published: no store, no internet, no account.

Today (`PARTIAL_0269`) the page is plain HTTP (decision of 2026-10-21, now revisited by the
maintainer on 2026-10-27), and the address, secret and token change at each run.

## Why HTTPS

A web app manifest is enough for a home-screen shortcut, but the install invitation (Chrome
on Android) and a service worker (the offline "mh is not running" page) need a secure
context. Over HTTP neither works (to check on the maintainer's phone, documented by
Chrome/WebKit). iOS never shows an install invitation: the page shows its own one-line hint
(Share > Add to Home Screen) on Safari when not already standalone.

## Design (approved by the maintainer, 2026-10-27; tests and measurements later)

1. **Local certificate authority, created once by mh.** A root CA (long validity) and a server
   certificate signed by it for the PC's LAN address (IP SAN). When the address changes, mh
   re-issues the server certificate only: the phone keeps trusting the CA. Library to check
   (`cryptography` vs `openssl` in the image: size cost to measure with `dive`).
2. **The phone installs the CA once**, from the pairing page served in HTTP on a second fixed
   port (download `media-hygiene-ca.crt` / iOS `.mobileconfig`, with the steps: Android
   Settings > Security > Install certificate; iOS profile + Settings > General > About >
   Certificate Trust Settings). Then the page redirects to HTTPS. Whether Chrome on Android
   trusts a user-installed CA for a PWA: to check.
3. **Fixed port and stable address.** A fixed port (a named constant; a setting only if it
   collides on some machine); the docs ask for a DHCP reservation in the box. `<pc>.local`
   (mDNS) as an alternative: support on Android/iOS to check.
4. **Durable pairing per phone.** The first time: the QR code/8-digit code as today. The
   server then draws a random token for that phone, keeps only its hash with a name and a
   date in the paired-phones file, and sets a long-lived `Secure; HttpOnly; SameSite=Strict`
   cookie. Next runs: no code. The home page lists the paired phones with "Forget this
   phone" (revocation); the wrong-code limit (`MAX_FAILURES`) stays.
5. **Manifest + service worker.** `manifest.webmanifest` (name, meerkat icon,
   `display: standalone`, `start_url: /`), the `apple-touch-icon` and
   `apple-mobile-web-app-*` tags. The service worker caches only the offline page and its
   icon (never photos, never API answers: the phone stays read-only — memory
   `phone-read-only`); on a failed navigation it shows the offline page, with Retry, and
   retries every few seconds.
6. **Say "Media Hygiene", show the meerkat (maintainer, 2026-10-27).** A newcomer must know
   at once what this is: every phone-facing text names the product "Media Hygiene" (FR:
   « Média Hygiène »), never the bare `mh` (the command is named only where it is typed).
   The offline page reproduces the meerkat (`assets/images/meerkat-asleep.webp`, cached by
   the service worker) with e.g. "Media Hygiene is asleep: it is not running on the PC.
   On the PC, start Media Hygiene (`mh`)". The app's name, icon (meerkat) and splash
   screen (manifest `name`, `background_color`, `icons`; iOS `apple-touch-startup-image`)
   say the same.
7. **One startup screen, on the phone and on the PC.** The same splash (meerkat + "Media
   Hygiene" + one line of what it does; the picture is `assets/images/meerkat-splash.webp`,
   chosen by the maintainer on 2026-10-27, no text in it: the page writes the words) on the phone app's launch and on the PC's home page
   while it loads, built from one shared template so both stay identical (memory
   `same-features-on-tile-pages`: same look on every page).

## Where the files live (approved by the maintainer, 2026-10-27)

- Not `/config` (config.toml and `people/` only).
- Not `/cache`: it may be emptied or restored (0352), which would force reinstalling the CA
  on every phone.
- Proposal: `C:\Users\<user>\media-hygiene\lan\` on the host (mh home: kept files only),
  mounted by `mh` as `/lan` (`Locations`, `MEDIA_HYGIENE_LAN_DIR`): `ca.key` (never served),
  `ca.crt`, `server.crt`/`server.key`, `phones.json`. Losing it means installing the CA and
  pairing again, nothing worse.

## Tests (this TODO)

Cert issued for the address and re-issued when it changes (CA unchanged); `ca.key` is never
served; the HTTP port serves only the CA download page and the certificate files, then
redirects to HTTPS; `/lan` resolved by `Locations` and mounted by `mh`. Docs in both
languages (the CA install steps per phone), `docs_screenshots` to run.

## Explicit NON-goals

- Durable pairing, the paired-phones list (0431).
- Manifest, service worker, offline page, splash (0432).

## Status — PARTIAL (2026-10-27)

### Done
- `/lan` mount point (`MountKind.LAN`, `Locations.lan_dir`, `MEDIA_HYGIENE_LAN_DIR`), shown
  only when mounted in `media-hygiene config`.
- `review/lan_tls.py`: local CA (EC P-256, 20 years, `ca.key` 0600) and a server certificate
  (IP SAN, 825 days) made by the `openssl` CLI of the image; re-issued only when the address
  changes (`server.address`), CA kept. No folder or no `openssl`: plain HTTP as before.
- `review/listen.py`: the home network's door in HTTPS; beside it a plain HTTP door
  (`LAN_CA_DOOR_PORT` 48089, published on `LAN_CA_PORT` 8089): `review/lan_ca_page.py` +
  `templates/lan_ca.html.j2` (steps Android/iOS, `ca.crt` as `application/x-x509-ca-cert`,
  every other path 303 to HTTPS; `ca.key` never served).
- `LanAccess.secure`: `https://` origin and QR/pair URL, `Secure` cookie, the PC's card says
  "First time on this phone? Install the certificate first: http://<address>:8089/".
- `mh_lan.ps1.j2`: `$HOME\media-hygiene\lan` mounted as `/lan` and port 8089 published for
  `home` only — the slideshow stays plain HTTP (a TV cannot install a CA: deviation from the
  TODO, which did not mention TVs).
- Address helpers moved to `review/lan_address.py` (`lan.py` was at 200/200).
- Docs en+fr `commands/home.md` (HTTPS row, "Once per phone: install the certificate", DHCP
  reservation), translations, `tests/unit/test_lan_https.py` (incl. a real TLS handshake).

### Not done
- The test on the maintainer's Android phone and on an iPhone: CA install, Chrome trusting a
  user CA, Docker Desktop publishing port 8089 on the LAN address, firewall prompt.
  **Reason:** needs the maintainer's PC and phones (a step of `tests/measure/mh-measure.ps1`
  to add with that test).
- iOS `.mobileconfig` download (Safari installs the `.crt` as a profile already).
  **Reason:** to add only if the iPhone test shows the `.crt` is not enough.
- `<pc>.local` (mDNS) as an alternative to the DHCP reservation.
  **Reason:** Android/iOS support to check on the devices first.
- `docs_screenshots` (the PC's card gained a line).
  **Reason:** heavy (image build + browser): run by the maintainer.
