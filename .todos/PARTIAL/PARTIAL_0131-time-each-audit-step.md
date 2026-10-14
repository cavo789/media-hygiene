# 0131 — Time each audit step, then measure a warm audit on the real collection

- **Priority**: High — the speed TODOs 0132–0136 are ranked on guesses until these numbers exist
- **Batch**: scan
- **Depends**: —
- **Files**: `src/media_hygiene/console/progress.py`, `src/media_hygiene/scan/progress.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/services/near_checks.py`, `src/media_hygiene/services/reporting.py`, `.todos/0104-maintainer-measurements-real-photos.md`

## Context

Speed review of 2026-10-14. The maintainer's first weeks reuse a single collection (`C:\Photos`,
about 70,000 files) for every command: `audit`, `review`, `review --near`, `clean`,
`crosscheck`, `classify`, `tags`, `people`. Nothing is added to it, and the only changes come
from `media-hygiene` itself (quarantine moves). TODO 0130 removed the walk of unchanged folders.
What a warm audit still spends its time on is unknown: `AuditFindings.seconds` is only a total.

Steps a warm audit runs (`services/audit.py`, `services/near_checks.py`,
`services/reporting.py`):

1. listing (0130: one `stat` per folder);
2. `forget_missing`;
3. integrity pass: one `SELECT` plus a pydantic parse per file (`scan/broken.py`);
4. exact duplicates: `get()` again per candidate (`scan/exact.py`);
5. `find_similar`, run twice (before and after colours);
6. colour measurement of every candidate, with nothing cached (see 0132);
7. `same_streams` payload digests (see 0132);
8. report: thumbnails decoded again (see 0133), HTML, CSV.

## What to do

1. Record the duration of each step: the progress sink already sees each `start`/`stop`. Add
   the steps that show no bar (similar search, report writing).
2. With `--verbosity verbose`, print one line per step after the findings table, e.g.
   `Listing 1.2 s · cache 3.4 s · similar 0.8 s · colours 21 s · report 9 s`. Users see where
   the time goes (pedagogy rule), and the maintainer can paste it.
3. Add a section to `0104-maintainer-measurements-real-photos.md`: run `audit` twice with nothing
   changed, then `review --near`, and paste the verbose step line of each run.
4. Re-rank 0132–0136 on those numbers (update their Priority lines).

## Acceptance

- `audit -v` prints the per-step durations; a unit test checks that every step is listed.
- The figures of a warm audit on the real collection are recorded in 0104 or here.

## Status — PARTIAL (2026-10-14)

### Done
- `scan/stopwatch.py`: `Stage` (listing, index upkeep, integrity checks, fingerprints, near
  duplicates, colours, same streams) and a `Stopwatch` that adds up each stage (the two
  `find_similar` runs count as one stage). `AuditService` times every stage
  (`services/audit_analysis.py` holds the integrity → digests pass, moved out of `audit.py`);
  `checked_similar` takes `NearTools` (colour tools + stopwatch). `AuditFindings.stages` holds
  the result.
- `--verbosity verbose`: `Time per step: listing 1.2 s · …` under the findings table
  (`console/stage_times.py`), and `Report written in 9.1 s.` after the report
  (`cli/flows.report_and_announce`). Translated; docs `start/01` and `commands/audit` en + fr.
- Tests: `tests/unit/test_stage_times.py`; `test_near_clean.py` checks every stage is on the
  verbose line of a real audit.
- Section 7 of `0104-maintainer-measurements-real-photos.md`: what to run and paste.

### Not done
- The figures of a warm audit on the real collection, and the re-ranking of 0132–0136 on them.
  **Reason:** needs the maintainer's `C:\Photos` (an unattended agent never reads it); see 0104 §7.
