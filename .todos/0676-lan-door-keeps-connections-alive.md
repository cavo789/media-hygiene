# 0676 — Phone and TV door: connections kept alive instead of one TLS handshake per request

- **Priority**: Medium
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/review/serving.py`, `src/media_hygiene/review/respond.py`, `src/media_hygiene/review/http.py`, `src/media_hygiene/review/listen.py`, `tests/unit/`
- **Needs maintainer**: the load of a 200-tile page on the phone over Wi-Fi, before and after (browser's network tab or a stopwatch)

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

The server answers one request per connection (`Connection: close`, `review/respond.py`).
On the PC's loopback that is free. On the home network's door every thumbnail, picture and
API call opens a TCP connection **and a TLS handshake** (0430).

*Measured* (devcontainer loopback, Python client, 6 parallel connections, 300 answers of
6.4 KB, best of 3, 2026-11-10 — script in the review's scratchpad):

| | close | keep-alive |
|---|---|---|
| plain HTTP | 0.08 ms / request | 0.02 ms |
| TLS (EC P-256) | **0.82 ms / request** | **0.04 ms** |

That is CPU only, on a PC. On a phone over Wi-Fi each new connection also costs about two
round trips before the first byte (*estimated* 5–20 ms each on a home network) and a
handshake on the phone's CPU: a 200-tile page pays it 200 times.

## Proposal

- HTTP/1.1 keep-alive in `serve_connection`: loop on requests of the same connection, an
  idle timeout (e.g. 15 s), a cap of requests per connection, `Connection: close` kept for
  errors and for a body sent by parts when the file shrank.
- With it, a cap on simultaneous connections per door (see the connection-limits TODO of
  the same review): kept connections must not exhaust it.
- The reload-on-new-run logic (`X-Media-Hygiene-Run`) is per answer: unchanged.

## Acceptance

- [ ] Unit tests: two requests on one connection; idle timeout; a malformed second request
- [ ] The phone's load of a 200-tile page before / after (maintainer)
- [ ] The slideshow on the TV (plain door) still works: a TV's browser may ignore keep-alive

## Where the user gains

Per request on the phone: 0.82 → 0.04 ms of server CPU (measured), plus about two round
trips saved (estimated); to confirm on the phone.
