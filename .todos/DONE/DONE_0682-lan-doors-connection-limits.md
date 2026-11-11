# 0682 — Home-network doors: limits on connections and slow requests

- **Priority**: Medium
- **Batch**: lan-security
- **Depends**: —
- **Files**: `src/media_hygiene/review/listen.py`, `src/media_hygiene/review/serving.py`, `src/media_hygiene/review/http.py`, `tests/unit/`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

Read in `review/listen.py`, `serving.py`, `http.py` (2026-11-10): each connection may take
30 s to send its request (`_TIMEOUT_SECONDS`), the body is capped (64 KB) and the headers
too — good — but **nothing caps the number of connections**, per door or per address, and
the limits are the same before and after pairing. One device on the Wi-Fi opening a few
thousand idle connections holds as many tasks and file descriptors for 30 s each, renewed:
the home page stops answering the PC too (same process), and a step followed in the page
looks dead. The photos are not at risk; the availability is.

Also unmetered before pairing: the TLS handshakes (CPU) and the pairing page.

## Proposal

- On the LAN doors only (the PC's loopback stays as it is): a cap of simultaneous
  connections per address (e.g. 16) and per door (e.g. 128); beyond it the connection is
  closed at once, counted, and said on the PC's card with the address.
- A shorter time to send the request line and headers on the LAN doors (e.g. 5 s), the 30 s
  kept for a body.
- A timeout on the TLS handshake (`ssl_handshake_timeout` of `asyncio.start_server`).
- Unpaired requests: answered from memory only (the pairing page rendered once), never the
  index nor the disk.
- Constants, not settings (nothing a collection changes); the figures tuned so that a phone
  loading a 200-tile page (6 connections) and a TV never meet them.

## Acceptance

- [ ] A test opening 500 idle connections on the LAN door: the PC's door still answers
      within its usual time, the surplus is refused
- [ ] A 200-tile page from one address is not slowed (test with 6 parallel connections)

## Where the user gains

Before: one misbehaving device can freeze every page, the PC's included. After: it is
refused and named on the PC's card.
