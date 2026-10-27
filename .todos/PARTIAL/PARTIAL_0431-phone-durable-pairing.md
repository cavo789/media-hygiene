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

## Status — PARTIAL (2026-10-27)

### Done
- `review/lan_phones.py`: `PhoneBook` over `/lan/phones.json` (id, name from the
  `User-Agent`, date, SHA-256 of the token only; atomic draft + rename, 0600; a missing or
  corrupt file lists nobody); `phone_book()` only under HTTPS.
- `review/lan_app.py`: the right code under HTTPS draws a token per phone and sets
  `Max-Age` 400 days (Chrome's cap), `HttpOnly; SameSite=Strict; Secure`; a phone is paired
  by the run's cookie or a listed token; `MAX_FAILURES` unchanged. Plain HTTP: as before.
- `review/lan_phones_api.py`: `GET /api/lan/phones`, `POST /api/lan/forget` (loopback only,
  JSON POST guard), the list answered after a forget is read back from disk.
- The PC's card lists "Phones paired for good" with "Forget this phone" (`home.js.j2`).
- `Pairing`/`pair_page` moved to `review/lan_pairing.py` (`lan_app.py` near the cap).
- Docs en+fr (`commands/home.md`), translations, `tests/unit/test_lan_phones.py`.

### Not done
- The test on the maintainer's Android phone: pair, restart `mh --lan`, reopen without a
  code; forget it from the PC.
  **Reason:** needs the maintainer's PC and phone.
- `docs_screenshots` (the card gained the phones list).
  **Reason:** heavy (image build + browser): run by the maintainer.
