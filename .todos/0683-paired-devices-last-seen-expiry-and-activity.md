# 0683 — Paired phones and TVs: last seen, expiry when unused, *Forget all*, and what each one did

- **Priority**: Medium
- **Batch**: lan-security
- **Depends**: —
- **Files**: `src/media_hygiene/review/lan_phones.py`, `src/media_hygiene/review/lan_phones_api.py`, `src/media_hygiene/review/lan_app.py`, `src/media_hygiene/review/templates/home.js.j2`, `tests/unit/test_lan_phones.py`

Filed by the UX / speed / security review of 2026-11-10 (asked by the maintainer; analysis only, no code changed).

## Context

A phone paired under HTTPS keeps a token for 400 days (0431); a TV is "paired for good"
(0456). Read in `review/lan_phones.py` (2026-11-10): `phones.json` keeps for each device an
id, a name taken from the `User-Agent` (`Android`, `iPhone`…), the pairing date and the
token's hash. Missing for a family that lends, sells or loses a phone, or pairs a guest's:

- no **last seen** date, no address: three devices all called `Android` cannot be told apart;
- no **expiry** when unused: a phone not seen for a year still opens the library;
- no **Forget all** (after a doubt: one click instead of one per device);
- no trace of **what a device read**: the user cannot answer "did someone look at the
  photos while I was away?".

A paired device reads the whole library, originals included when `[review]
lan_phone_originals` is on.

## Proposal

- `phones.json` / `tvs.json`: `last_seen` (written at most once an hour per device, atomic
  as today), the last address, a name the user may type on the PC's card.
- A device unseen for 90 days is forgotten at the next start, said on the card (*estimated*
  default; a constant — say in the report whether families want a setting).
- *Forget every device* on the card (ask dialog), read back from disk.
- An activity line per device, kept small: per day, pages opened and pictures served
  (counts, never which photos), 30 days, in `/lan/activity.json`; shown on the card.
- A device forgotten while connected loses access at its next request (already so: the
  file is read on each question — keep a test).

## Acceptance

- [ ] The card lists name, paired on, last seen, address; rename and forget read back
- [ ] Expiry tested with a clock; *Forget all* tested
- [ ] What happens when `/lan` moves or is restored from an older copy: written and tested
      (workflow rule for anything stored by path)
- [ ] Docs EN + FR

## Where the user gains

Before: a lost or lent phone keeps access up to 400 days unless the user remembers to
forget it, and nothing tells devices apart. After: unused access ends by itself (90 days),
and the PC shows who came and when.
