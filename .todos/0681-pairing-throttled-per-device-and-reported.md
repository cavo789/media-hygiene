# 0681 — Pairing: wrong codes throttled per device and reported on the PC, never a lock-out for all

- **Priority**: Medium
- **Batch**: lan-security
- **Depends**: —
- **Files**: `src/media_hygiene/review/lan_pairing.py`, `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/lan_card.py`, `src/media_hygiene/review/templates/lan_pair.html.j2`, `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/review/serving.py`, `tests/unit/test_home_lan.py`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

Read in `review/lan_pairing.py` (2026-11-10): the pairing counts wrong codes **for the whole
server** (`MAX_FAILURES = 5`), then closes "until `mh --lan` is typed again". Two effects:

- **Lock-out by anyone**: any device on the Wi-Fi (a guest's phone, a hacked box, a child)
  closes the pairing for the family with five requests to `/pair/00000000`. The user must
  go to the PC and restart `mh`.
- **Nothing is said on the PC**: the attempts leave no trace the user sees — the very
  signal of "an unauthorised device is trying" the maintainer asks about.

(The counter is also reset by each restart of the home server; with 10^8 codes and 5 tries
a run that is not a practical way in — said for completeness.)

## Proposal

- Count per client address: after 3 wrong codes from one address, that address waits (30 s,
  doubling, capped); a global ceiling (e.g. 20 wrong codes per run) still closes the
  pairing, as the last resort. The connection's peer address must reach the handler (today
  a `Request` does not carry it).
- The PC's card shows it: *⚠ 5 wrong codes from 192.168.1.37 at 14:02* with *Open pairing
  again* (a new code, no restart of `mh`) and *It was me*.
- A new device paired is said on the PC's page (toast) and in the paired list with its date.
- Decide whether `MAX_FAILURES` and the delays stay constants (proposed: yes — nothing a
  collection changes).

## Acceptance

- [ ] Five wrong codes from one address do not prevent another address from pairing (test)
- [ ] The PC's card lists the attempts, read back from the server; *Open pairing again*
      gives a new code that works
- [ ] Docs EN + FR (`commands/home.md`)

## Where the user gains

Before: 5 requests from any device lock the pairing until `mh` restarts, silently. After:
the family is never locked out, and an attempt is shown on the PC with its address.
