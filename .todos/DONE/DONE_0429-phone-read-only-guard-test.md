# 0429 — A guard test: no write route reachable from a phone, and no write button shown there

- **Priority**: Medium
- **Batch**: home
- **Depends**: 0427
- **Files**: `src/media_hygiene/review/lan_paths.py`, `tests/unit/`, `src/media_hygiene/review/templates/`, `src/media_hygiene/search/`, `src/media_hygiene/share/templates/`

## Why

Product rule decided by the maintainer (2026-10-27): **anywhere but the PC, everything is
read-only**. `lan_paths.py` enforces it today by an explicit list, but nothing stops a future
route that writes from being added to it by mistake, and nothing checks that the phone's pages
hide the buttons that would end on a 403 (a button that fails is a UX bug).

## What

1. Every route that changes something (set aside, *Apply now*, a move, a rule, a name, a
   decision file, `config.toml`) declares it (a flag or a set next to its path); a unit test
   walks every app's routes and fails if one of them is in the phone's list (`READ_PATHS`,
   `READ_PREFIXES`, `phone_may`), whatever `[review]` setting is on.
2. A test per tile page served to a phone (home, search, browse, albums): rendered for the LAN
   door, it carries no write control (set aside, apply, move…). Check the templates
   (`pick_*` — skill `photo-picking-pages`) and hide what the phone may not do.
3. Integration test, as `curl`/`wget` would do it: real `POST`s to each write route through the
   LAN door (`Door.LAN`), without the pairing cookie then with a valid one: 403 both times
   (one parametrised test). The pairing cookie never opens a write.
4. Docker: a test of the command `mh` builds (`services/launcher.py`) that the PC's door is
   always published as `127.0.0.1:<port>`, never on every interface. It is the one weak point of
   the two-door model: published on `0.0.0.0`, any device of the Wi-Fi would reach the PC's
   door. Only the LAN door (`mh --lan`) may be published beyond the loopback.

No tokens nor profiles (decided 2026-10-27): the PC is told by the socket a request came in by,
never by a secret; a token would only matter if a remote write were allowed, which it never is.

## Acceptance

- Adding a write route to the phone's list makes the test suite fail.
- The phone's pages show no action, button or menu link leading to a write.
- A `curl` from the home network gets 403 on every write route, paired or not.
- Publishing the PC's door beyond `127.0.0.1` makes the test suite fail.
