# 0629 — `tags --meaning` announces about half of the time it takes

- **Priority**: Low — the work is resumable, but a wrong figure misleads who plans around it
- **Batch**: meaning
- **Depends**: —
- **Files**: `src/media_hygiene/services/meaning.py`, `src/media_hygiene/meaning/clip.py`, `tests/unit/test_meaning_service.py`

## Problem

Measured by the maintainer on 2026-11-06 (console output): 33,660 photos announced at "about 18 min 26 s" (0.033 s per photo), done in 34 min 20 s (0.061 s per photo), a factor of 1.9.

## Lead (read in the code, not verified)

`estimate` uses `store.seconds_per_photo()`, else `SECONDS_PER_PHOTO`. Identical copies are stored with a time of `0.0` (`services/meaning.py`, "a copy: no time of its own"): if the average counts them, it is too low. Machine load between runs may also play.

## To do

Find the cause by measuring, fix it, and test that copies do not lower the pace. The documentation's figures ("about 1 minute for 1,000 photos") should be checked at the same time, in both languages.
