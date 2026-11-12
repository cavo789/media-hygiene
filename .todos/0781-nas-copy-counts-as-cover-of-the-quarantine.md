# 0781 — A NAS copy counts as cover of a file set aside

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/services/push_proof.py`, `src/media_hygiene/services/push_listing.py`, `src/media_hygiene/services/only_copies.py`, `src/media_hygiene/services/only_count.py`, `src/media_hygiene/services/safety_cache.py`, `documentation/en/commands/push.md`, `documentation/fr/commands/push.md`
- **Needs maintainer**: a decision: what proves a NAS copy (same relative path, size and date as push compares them, or the full digest read by Windows) and whether it stops counting once the next push moves it into `.removed` (kept 90 days)

Left by 0775 (from 0688, option B decided on 2026-11-10: count, do not copy).

## Context

A file of the quarantine is *covered* today only when it was set aside as an exact copy and its
kept twin is still on the disk (`services/only_copies.py`, `only_count.py`). A photo pushed to the
NAS **before** it was set aside (a near duplicate, a burst shot) still has its NAS copy until the
next push moves it into `.removed`, yet `purge`, `push`, the *Disk space* page and the home card
count it as existing nowhere else. The container keeps no listing of the target after a push
(`push_listing` is built during the run only), so nothing can tell.

## Proposal

- At the end of a proven push (`push_proof.prove_push`), keep in `/cache` the target's entries
  that match a file of the quarantine (its journal `path` relative to the target: size, date), with
  the push's run and date; read by `only_copies`/`only_count` as a cover, the cache key of
  `safety_cache` widened to that file.
- Said apart: *N exist nowhere else, M only on the NAS* (a cover that leaves with `.removed`).

## Acceptance

- [ ] Test on the demo tree: a near duplicate pushed then set aside counts as covered; set aside
      before any push, it counts as an only copy; a push moving it into `.removed` changes the count
      as decided
- [ ] Every event that invalidates the kept listing tested (a new push, a purge, an undo, the
      target changed with `--to`)
- [ ] Docs EN + FR (`push.md`, `purge.md`, `reference-safety.md`)
