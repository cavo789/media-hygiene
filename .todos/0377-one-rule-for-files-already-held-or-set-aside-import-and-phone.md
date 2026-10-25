# 0377 — One rule for "already held or set aside on purpose", shared by `import` and `phone`

- **Priority**: Medium
- **Batch**: import
- **Depends**: —
- **Files**: `src/media_hygiene/services/phone_known.py`, `src/media_hygiene/services/phone_holdings.py`, `src/media_hygiene/services/phone_plan.py`, `src/media_hygiene/services/backup_dealt.py`, `src/media_hygiene/services/returned.py`, `src/media_hygiene/plan/backup_import.py`, `src/media_hygiene/plan/returned.py`, `src/media_hygiene/index/gone_rows.py`, `src/media_hygiene/services/import_plan.py`

## Why

Seen 2026-10-25 while comparing `mh import` (0245) and `mh phone` (0219, 0248), agreed by the
maintainer: both answer the same question, *does the user already hold this file, or did they
set it aside on purpose?*, written twice:

- `import`: `backup_dealt.py` — `ReturnedFinder` (contents the journals remember: set aside by a
  choice, deletions confirmed) **plus** the deletions waiting for `review --gone`
  (`index/gone_rows.gone_records`, 0224).
- `phone`: `phone_known.py` — the index by name and size, `remembered_of` (shared with
  `returned`), its own reading of the runs, quarantines and purge dates (`runs_in`,
  `purge_dates`, `mounted_quarantines`); then `phone_holdings.py` for the content.

Part is shared already (`remembered_of`). A divergence *to check*: `phone_known.py` does not
import `gone_rows`, so a photo deleted in the Explorer, waiting for `review --gone`, may be
proposed again by `mh phone` while `mh import` leaves it out. A rule fixed on one side only
is the risk.

What differs for a real reason and stays apart: the phone gives a **name and a size only**
(MTP: reading the content means copying the file), a folder gives the content. So the key
differs (name + size first, then the staged copy's SHA-256 for `--free`; the digest at once for
a folder); the *reasons* (held, set aside and why, deleted, waiting for `review --gone`) must
not.

## What to do

1. Write down, from the code, each reason each side gives and from which source (a table in
   the commit message): what only one side knows is the list of bugs to fix.
2. One module of reasons (`services/dealt_with.py` or extend `backup_dealt`), asked with a key
   that is either a content (size + digests) or a name + size (the phone's first pass); both
   commands read their answers from it and keep only their own key-building.
3. A test per reason run through **both** commands (a parametrised test over the two sources):
   set aside by `clean`, in quarantine, purged since, exact copy deleted, deleted in the Explorer
   confirmed, waiting for `review --gone`, a run undone since (no reason: the file came back).
4. Same messages on both sides (one `_()` string per reason).

## Acceptance

- The reasons table of point 1 has no line known by one command only.
- A file deleted in the Explorer, then found on the phone **and** on the NAS: both commands
  leave it out and say why, in the same words.

## Gain

One place to fix a rule instead of two; the gap found in point 1 fixed (*to check*: the
`review --gone` case above). No speed change expected (*estimated*: the same reads).
