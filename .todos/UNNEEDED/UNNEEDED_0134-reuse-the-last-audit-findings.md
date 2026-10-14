# 0134 — Reuse the last audit's findings when nothing changed since

- **Priority**: High — `review`, `review --near`, `clean` and `crosscheck` each run a full audit again, right after the `audit` that found the same thing
- **Batch**: scan
- **Depends**: 0131
- **Files**: `src/media_hygiene/services/audit.py`, `src/media_hygiene/cli/flows.py`, `src/media_hygiene/plan/models.py`, `src/media_hygiene/index/schema.py`, `src/media_hygiene/index/repository.py`, `src/media_hygiene/services/listing.py`, `documentation/en/start/02-keep-the-cache.md`, `documentation/fr/start/02-keep-the-cache.md`

## Context

Speed review of 2026-10-14. `cli/flows.audit_and_show` is the first step of `audit`, `clean`,
`crosscheck` and `review` (both modes). A typical session is `audit` → `review --near` →
`clean --tier near` → `audit`. Each run repeats every step after the listing: index reads for
every file, the exact-duplicate pass, `find_similar` twice, and colours (until 0132). Yet in the
maintainer's use case nothing changes between two runs, except what `media-hygiene` itself moves.

After TODO 0130 the listing is cheap and tells exactly which files exist, with their size and
mtime. That listing, together with the settings that shape an audit, determines its findings.

## What to do

1. Fingerprint of an audit: a digest of the sorted (path, size, mtime_ns) of the listing, plus the
   sidecars, plus the settings that change findings: folders (prefer/protect/exclude),
   extensions, excluded names, near thresholds, keep policy. Also the application version and the
   `ffmpeg`/`ffprobe` availability.
2. After an audit, save the findings next to the index (`/cache/findings.*`, never `/config`),
   with their fingerprint. The format must be versioned and safe to load: JSON or a pydantic
   model, not `pickle`. A tampered `/cache` must not execute code.
3. Next audit: walk, compute the fingerprint, and on a match load the findings and skip steps
   2–7 of 0131. Print one line, as 0130 does: "Nothing changed since the audit of 14/10 at 21:05:
   its findings are reused." Add the 💡 for `audit --full`, which ignores the saved findings.
4. Any change (a file added, removed or touched, a setting changed) runs the audit as today and
   replaces the saved findings. `clean` keeps its byte compare before each delete, so stale
   findings can never delete a wrong file.
5. The report is still written (a new folder per run). With 0133, its previews cost nothing.
6. Docs en + fr: what is reused, and when it is not.

## Open question for the maintainer

Should a full audit that finds a reusable snapshot still say how old it is, and offer `--full`
after N days (as `full_check_days` does for listings)? Proposal: yes, with the same setting.

## Acceptance

- `audit` twice in a row: the second one skips the analysis. A test counts the calls of
  `BrokenFileFinder.find`.
- Changing `--prefer`, adding a file, or touching one makes the next audit run in full.
- Measured with 0131: time of a second `audit` and of `review --near` on the real collection,
  before and after.

## Status — BLOCKED (2026-10-14)

### Not done
- All items remain open.
  **Reason:** it depends on the numbers of 0131, which only the maintainer can measure
  (`0104` §7: `mh --verbosity verbose audit` twice, then `review --near`). The only figure so far
  (0104 §3, 2026-10-12, before 0130) is a warm audit of 52,056 files in **10 s in all**. Saving
  and reloading every finding (plan, groups, near decisions, bursts, video looks, inventory)
  safely, without `pickle`, is a large, risky surface: build it only if the step line shows
  that what it skips (`checks`, `fingerprints`, `near duplicates`, `colours`, `same streams`)
  still costs much once 0132 caches colours and stream digests and 0135 reads the index once.
  The open question above (age of the snapshot, `--full` after `full_check_days`) also waits
  for the maintainer.

## Status — UNNEEDED (2026-10-14)

The figures it waited for (DONE_0131): a warm audit of 52,056 files takes 3–4 s; what this
TODO would skip (`cache` 0.8 s, `checks` 0.1 s, `fingerprints` 0–0.2 s, `near duplicates`
1.5 s) is about 2.5 s per command. Saving and reloading every finding safely, with the risk of
stale results, is not worth it. Decided with the maintainer. Revive only if a warm audit of a
much larger collection spends tens of seconds in those steps.
