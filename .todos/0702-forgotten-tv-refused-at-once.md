# 0702 — A TV forgotten on the PC is refused at its next request, like a phone

- **Priority**: Medium
- **Batch**: lan-security
- **Depends**: —
- **Files**: `src/media_hygiene/slideshow/screens.py`, `src/media_hygiene/review/lan_phones.py`, `tests/unit/test_lan_devices.py`

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0683 (commit e00417d8) found that `Screens.is_paired` keeps a TV's token in memory: a TV
forgotten on the PC keeps the slideshow until `mh` restarts. Decided: refuse it at once.
`slideshow/screens.py` is at the 200-line cap: split it first. Also record the TVs' last seen
(left undone by 0683 for the same reason).

## Acceptance

- [ ] A forgotten TV gets the pairing page at its next request (test)
- [ ] TVs' last seen recorded at most once an hour
