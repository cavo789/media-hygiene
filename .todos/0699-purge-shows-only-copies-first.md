# 0699 — `purge` shows the files with no other copy before its first question

- **Priority**: Medium
- **Batch**: safety-net
- **Depends**: —
- **Files**: `src/media_hygiene/actions/purge.py`, `src/media_hygiene/services/disk_purge.py`, `src/media_hygiene/cli/`, `tests/integration/test_only_copies.py`

Decided by the maintainer on 2026-11-11, review of the iterate of 2026-11-10 (PR #77).

## Context

0688 (commit f3ffdef4) lists the quarantine's only copies and asks for them apart, **after** the
first question. Decided: show them **first**, then one informed decision (seeing first, 0524),
in the console and on the purge page.

## Acceptance

- [ ] Console and page: the only copies listed before any question; one question then
- [ ] Answering no erases nothing (test kept)
- [ ] Docs EN + FR (`commands/purge.md`); `docs_screenshots` should run
