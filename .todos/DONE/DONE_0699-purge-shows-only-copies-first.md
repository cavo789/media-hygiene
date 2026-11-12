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

- [x] Console and page: the only copies listed before any question; one question then
- [x] Answering no erases nothing (test kept)
- [x] Docs EN + FR (`commands/purge.md`); `docs_screenshots` should run

## Result (2026-11-12)

Console: `purge` lists the only copies (20 by name, the rest counted) after its warnings and
before its one question, which names them ("That includes the N files listed above…").
Page: `GET /disk-space/api/only?run=` (`services/disk_only.py`); the quarantine page lists
them above its Erase button, the one question names them; no list read → no button.
Tests: `test_only_copies.py` (one question, list before it, no erases nothing; none → plain
question; the endpoint). `docs_screenshots` should run (purge console block).
