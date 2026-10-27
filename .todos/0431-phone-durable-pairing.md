# 0431 — A phone paired once stays paired (paired-phones file, "Forget this phone")

- **Priority**: Medium
- **Batch**: phone
- **Depends**: 0430
- **Files**: `src/media_hygiene/review/lan.py` (200/200: new module, e.g. `review/lan_phones.py`), `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/templates/lan_pair.html.j2`, the home page's "On your phone" card (`review/templates/`, `review/home_*`), `documentation/en/`, `documentation/fr/`
- **Needs maintainer**: a test on the maintainer's Android phone (pair, restart `mh`, reopen without a code)

## Goal

Point 4 of the design approved on 2026-10-27 (split from 0430, which has the full design):
the first time, the QR code / 8-digit code as today; the server then draws a random token
for that phone, keeps only its hash with a name and a date in `/lan/phones.json` (0430's
folder), and sets a long-lived `Secure; HttpOnly; SameSite=Strict` cookie. Next runs: no
code. The PC's home page lists the paired phones with "Forget this phone" (revocation);
the wrong-code limit (`MAX_FAILURES`) stays.

## Tests

A paired token survives a restart; a forgotten one is refused; only hashes are written;
`phones.json` written atomically and read back before "Forgotten" is shown; a missing or
corrupt file means pairing again, never a crash.

## Explicit NON-goals

- HTTPS, the CA, `/lan` (0430). Manifest, service worker, splash (0432).
