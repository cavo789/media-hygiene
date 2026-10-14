# 0160 — A first audit in stages: the exact duplicates first, in minutes; the decoding after

- **Priority**: Medium — on a collection of 300,000 photos the first audit takes hours before any report; most users come for the exact duplicates, which need no decoding
- **Batch**: scan
- **Depends**: 0159
- **Files**: `src/media_hygiene/services/audit.py`, `src/media_hygiene/services/audit_analysis.py`, `src/media_hygiene/scan/broken.py`, `src/media_hygiene/scan/exact.py`, `src/media_hygiene/scan/whole_read.py`, `src/media_hygiene/cli/cmd_audit.py`, `src/media_hygiene/report/`, `documentation/en/start/01-first-audit.md`, `documentation/fr/start/01-first-audit.md`
- **Needs maintainer**: a decision on the option (below), after the measurements of `tests/measure/mh-measure.ps1`

## Context

Proposed on 2026-10-14, accepted by the maintainer as a TODO. Today a first audit decodes every
picture (integrity, visual facts, metadata), then finds the exact duplicates, then the near
ones; the report comes at the very end. For a large collection on a Windows folder that is hours
(estimated from measured throughputs: ≈ 30 min of reading for 300,000 photos of 2.8 MB, more for
HEIC). Exact duplicates only need sizes and digests: same-size files are rare apart from real
copies, so a size grouping and a partial digest (128 KiB per candidate) find them in minutes.

The catch: since 0148 the full digest of a picture comes from the same reading as its decoding.
Finding the exact duplicates first means reading their full bytes before decoding them, then
again when decoding — the second reading 0148 removed, for the duplicates at least.

## Options (the maintainer decides)

1. **`audit --quick`**: sizes and digests only — exact duplicates, a report and `clean` usable
   at once; no integrity check, no near duplicates, no metadata. A later `audit` decodes
   everything (reading the duplicates a second time). Simple; the user chooses.
2. **Stages inside one audit**: stage 1 (sizes, partial then full digests of the candidates,
   a first report of exact duplicates, written before the decoding starts); stage 2 the
   decoding of the rest, the duplicates' bytes read again. One command; the report is
   rewritten at the end.
3. **Order only**: decode the same-size candidates first (their digests come from that
   decoding, 0148 kept), and write a partial report of exact duplicates as soon as they are
   done; the rest is decoded afterwards. No second reading, but the first report waits for
   the decoding of the candidates (a fraction of the collection).
4. Nothing: the ETA and the reassurance of 0159 are enough.

Measure first (the step line of a first audit, `mh-measure.ps1` step 1) to know how much of a
first audit the decoding is, against the reading.

## Acceptance

- The decision written here; then a first audit of a large test folder shows its exact
  duplicates (report, `clean` possible) in a fraction of the time of the full audit, figures
  measured before and after.

## Status — UNNEEDED (2026-10-14)

**Decision (maintainer, 2026-10-14): option 4, nothing more.** The figures it waited for
(`mh-measure.ps1` step 1, Windows + Docker Desktop, fresh cache): a first audit of 12,000 JPEG
photos (12.9 GB) in 30 s, checks 27.8 s, ≈ 465 MB/s; 4,000 photos (2.7 GB) in 9 s. For 300,000
photos of 2.8 MB that is ≈ 30 min (*estimate*, linear from these throughputs), not hours, and
0159's announcement ("… to check for the first time: less than a minute", measured 30 s) tells
the user beforehand that stopping is safe and the next audit takes seconds. Stages would read
the duplicates twice (undoing part of 0148) for a gain no longer worth the complexity. HEIC
stays slower (0155, blocked). Revive with a fresh TODO if a user finds a first audit too long.
