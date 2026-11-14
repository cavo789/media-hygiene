# 0819 — Safety card: a cache key that does not walk the quarantine

- **Priority**: High
- **Batch**: page-speed
- **Depends**: 0692
- **Files**: `src/media_hygiene/services/safety_cache.py`, `tests/unit/test_safety_cache.py`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: step 46 of `mh-measure.ps1` again after the change (Windows + Docker Desktop)

Filed 2026-11-14 from step 46 on the maintainer's PC.

## Context

*Measured* (step 46, maintainer's PC, real folders, two calls in the running home page):
`GET /api/safety` 11.86 s from Windows; inside, the card 10.7 s / 10.6 s, of which
`safety_key` 10.0 s each time. The key (`safety_key`) walks every folder below each run's
quarantine folder (`_tree`: `os.walk` + `stat`), through the Docker Desktop bind mount. The
cache of 0692 therefore costs what it saves. The user does not see it (the card is drawn from
`localStorage` first), but every opening of the home page, PC or phone, spends ~10 s of disk
on the quarantine, and a first opening on a new device waits for it.

## Proposal

Key on what changes when the quarantine changes through the tool: each run's journal stamp
(already there), the run folders' own stamps (one `stat` each, not their subtrees), the
index and the cover file. Moves by the user inside the quarantine are the gap to weigh: list
each event (file removed by hand, `purge`, `undo`, folder renamed) and say which one the key
still sees; the known lag of 0692 (counted until the next audit) may cover them.

## Acceptance

- [ ] `safety_key` under 0.5 s on the maintainer's PC (step 46), card under 1 s warm
- [ ] One test per invalidation event kept or dropped, the dropped ones written in the docstring
- [ ] Same facts as before (equivalence test on the demo tree)

## Status — PARTIAL (2026-11-14)

### Done
- `safety_key` walks the quarantine folders (`_tree`) only when the count asks the disk
  (no index, `/cache` not kept). With an index the count reads journals and index alone
  (`only_count`), so the walk bought nothing there: the key keeps the runs, each journal's
  stamp, the NAS cover and the index stamp.
- Events, with an index: a file set aside removed by hand in Explorer no longer refreshes
  the card at once (seen at the next audit, which stamps the index; the count never looked
  at that file anyway); `clean`, `undo`, `purge`, journal restored or lost, quarantine
  plugged in still do (their tests unchanged). Without an index: as before.
- Test `test_indexed_key_does_not_walk_the_quarantine` (no walk; a hand removal keeps the
  key; an audit changes it). 29 tests of the module and its importers pass.

### Not done
- Step 46 again on the maintainer's PC: `safety_key` expected under 0.5 s (*estimated*: what
  remains is one `stat` per run journal, 83 runs, plus two files; measured before: 10.0 s).
  **Reason:** only the maintainer's machine (Windows + Docker Desktop, real quarantine).
