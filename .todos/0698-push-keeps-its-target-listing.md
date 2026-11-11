# 0698 — `mh push` keeps the listing of what the NAS holds: a NAS copy counts as another copy

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/services/push_listing.py`, `src/media_hygiene/services/push_proof.py`, `src/media_hygiene/services/quarantine_ledger.py`, `src/media_hygiene/services/safety.py`
- **Needs maintainer**: a `mh push` run on Windows to the real NAS after the change (a step of `mh-measure.ps1`)

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0688 (only copies before `purge`) and 0689 (safety card) count a quarantined file as covered
only when its exact twin is still on the PC: the container keeps no listing of the push target.
Decided: `push` saves its proven listing (path, size, date, ends' digest) in `/cache`, and the
only-copy count and the card read it.

## Acceptance

- [ ] The listing written after a push is proven, with its date; stale after a newer push only
- [ ] A file already on the NAS is no longer an only copy (test with a fake listing)
- [ ] The card's "files newer than the last push" read from it instead of index dates
- [ ] What happens when the NAS folder moves or the target changes: written and tested
