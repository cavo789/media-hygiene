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
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
- [ ] Expiry tested with a clock; *Forget all* tested
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
- [ ] What happens when `/lan` moves or is restored from an older copy: written and tested
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
      (workflow rule for anything stored by path)
- [ ] Docs EN + FR
  → code work, not the maintainer's: listed in 0718 (2026-11-12)

## Where the user gains

Before: a lost or lent phone keeps access up to 400 days unless the user remembers to
forget it, and nothing tells devices apart. After: unused access ends by itself (90 days),
and the PC shows who came and when.

## Status — PARTIAL (2026-11-10)

### Done

- `phones.json`/`tvs.json`: `last_seen` (at most once an hour, or on an address change) and
  `address` (from the socket); older files load (`lan_phone_model.py`, defaults).
- Rename, *Forget every device* (in-card confirmation, no `window.confirm`), both read back
  from disk (`lan_phone_care.py`, `lan_phones_api.py`, `home.js.j2`).
- Expiry: `EXPIRY_DAYS = 90` at start (`phone_book`), said on the card; a phone without
  `last_seen` (old or restored file) is dated, never forgotten; TVs never expire.
- `lan/activity.json` (`lan_activity.py`): pages opened and pictures viewed (previews,
  originals, videos; thumbnails not counted), per day, 30 days, in memory, written every
  5 minutes at most, merged with the file, forgotten phones dropped.
- Tests `tests/unit/test_lan_devices.py` (clock injected, restore, moved folder, forgotten
  while connected); docs EN + FR (`commands/home.md`).

### Not done

- Flush of the activity counts at stop.
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  **Reason:** `LanApp` has no stop hook; a stop loses at most the last 5 minutes of counts.
- TVs' `last_seen`: not written (`slideshow/screens.py` at 199 lines caches tokens in memory).
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  A TV forgotten on the PC keeps the show until mh restarts (cached in `Screens._paired`),
  contrary to the TODO's "already so" claim — to fix in a follow-up.
  **Reason:** file at the size cap; needs a split first.
- Documentation screenshots: `docs_screenshots` should run (the card changed).
  → captures: one run of `docs_screenshots`, tracked in 0717 (2026-11-12)

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
