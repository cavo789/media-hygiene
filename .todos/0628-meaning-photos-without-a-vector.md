# 0628 — `tags --meaning` cannot decode photos the audit calls readable

- **Priority**: Medium — those photos can never be found by meaning, and nothing says which ones
- **Batch**: meaning
- **Depends**: —
- **Files**: `src/media_hygiene/services/meaning.py`, `src/media_hygiene/cli/meaning_flow.py`, `tests/unit/test_meaning_service.py`

## Problem

Seen by the maintainer on 2026-11-06 (image 0.4.0, measured from the console output): `mh tags --meaning` ends on "539 photos could not be decoded: they have no vector", out of 33,660, while the audit run just before reports 0 broken files. The cause was not looked for.

## To do

1. Find what these files are and why the audit's decode accepts them (RAW? HEIC? a truncation tolerance? a size limit?). The cause decides the fix.
2. Decode them when the audit can; otherwise, name them: a count alone leaves the user nothing to act on.
3. Check that they are not retried for nothing at each run, or say why they are.

## Needs maintainer

Their list on the real collection, once step 2 can show it.
