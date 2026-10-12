# 0109 — The Czkawka "second opinion" tip crowds out the useful ones on a small first audit

- **Priority**: Low — noise on the first screen
- **Batch**: guidance
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_audit.py`, `src/media_hygiene/cli/audit_actions.py`, `tests/unit/test_audit_actions.py`

## Context

UX review of 2026-10-12. On a small audit (one group of copies, no cache, no reports folder
mounted), the two tips kept were *Choose which folders keep their copies* and *Second opinion:
run Czkawka…*, followed by a 400-character `docker run … jlesage/czkawka … -x
3g2,3gp,arw,…` line and "(1 more tip: add --verbosity verbose to see it.)". For a first-time
user, a second tool before having tried the first one is noise, and that block is the longest
thing on screen. The cache and reports ⚙️ hints, which save them time at once, are the ones that
should win.

## Goal

- Rank the Czkawka tip below the setup hints (cache, reports, time zone) and below *prefer*; show
  it by default only before a `clean` of many files, or with `--verbosity verbose`.
- Keep `crosscheck` reachable: the `clean` confirmation can name it in one short line (it does in
  French already: *Si vous souhaitez un second avis, lancez 'crosscheck'*).

## Acceptance

- Unit test of the ranking: a first audit without cache shows the cache hint and not Czkawka.
