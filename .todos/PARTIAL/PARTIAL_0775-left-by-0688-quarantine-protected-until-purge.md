# 0775 — What 0688 left: The quarantine is covered by the NAS copy, or `purge` says what has no other copy

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `.todos/DONE/0688-quarantine-protected-until-purge.md`, `src/media_hygiene/services/push_sources.py`, `src/media_hygiene/services/push_listing.py`, `src/media_hygiene/services/push_lines.py`, `src/media_hygiene/services/quarantine_ledger.py`, `src/media_hygiene/actions/purge.py`, `src/media_hygiene/services/disk_purge.py`

Split from section 0688 of PARTIAL 0718 (`.todos/PARTIAL/PARTIAL_0718-code-left-in-partial-todos.md`), as decided by the maintainer in the review of 2026-11-12 (one TODO per remaining section). Source TODO: `.todos/DONE/0688-quarantine-protected-until-purge.md`.

## Left (as listed in 0718; the source TODO has the full wording)

- The figure on the quarantine page, the disk-space page and in `mh push`'s lines.
- A NAS copy counted as cover.
- The only copies are asked after the general purge question, not shown before it.
- The count of only-copy files shown before a purge, proven on the demo tree (a near
- With A: a push after a clean copies the run's quarantine; after a purge it leaves
- Docs EN + FR (`push.md`, `purge.md`, `reference-safety.md`)

## How to proceed

- Check each item against the code first: some may be done already and only unticked (then say so and close them).
- File follow-ups for what is really left; every figure says *measured* or *estimated*; a new limit: say whether it should be a setting.
- Documentation EN + FR and French strings when something user-facing changes.

## Status — PARTIAL (2026-11-12)

### Done
- The figure on the *Disk space* page: each run says how many of its files exist nowhere else
  (column *Nowhere else*, counted from the index by `disk_only.only_by_run`: one query per run, no
  stat per file; a run without journal counts every file, as `purge` does; no index: `?`), and the
  total under the title (`services/disk_space.py`, `disk_space.html.j2`).
- `mh push`'s plan says how many files set aside exist nowhere else and that the backup does not
  copy the quarantine (`cli/push_only.py`, read through the home card's cache `safety_cache`).
- Already done, checked against the code: the only copies shown before purge's one question
  (0699: `cli/purge_only.py`, the quarantine page's purge), and proven on the demo tree
  (`tests/integration/test_only_copies.py`: a near duplicate counted, an exact copy not).
- Option A (push copies the quarantine): not chosen (option B decided on 2026-11-10): obsolete.
- Tests: `test_only_copies.py` (disk space per run and total, journal lost, no index; push's line).
- Docs EN + FR: `commands/home.md` (Disk space), `commands/push.md`, `reference-safety.md`.

### Not done
- The figure on the quarantine page (`mh undo --pick`, a tile page) → filed as 0782.
  **Reason:** the run of 2026-11-12 held every tile page back for PR #80 (it touches
  `quarantine.html.j2`).
- A NAS copy counted as cover → filed as 0781.
  **Reason:** needs push to keep a listing of the target, and a decision on what proves a NAS
  copy and how long it counts (`.removed` keeps it 90 days).
- `docs_screenshots` should run (Disk space page, push's plan): tracked in 0717.
