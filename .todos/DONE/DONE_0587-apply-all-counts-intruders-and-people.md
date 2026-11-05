# 0587 — "Apply all" on the home page also counts the intruders and the people set aside

- **Priority**: Medium
- **Batch**: home
- **Depends**: 0522 (DONE)
- **Files**: `src/media_hygiene/cli/home_pending.py`, `src/media_hygiene/services/apply*`, the intruders and people decision files, `tests/unit/`

## Decided (maintainer, 2026-11-03, review of PR #61)

0522 counts every page writing `decisions.json`; the intruder files and the faces set aside on
`people` live in other files, so they were left out. Count them too (read from disk), and apply
them in the same one run, undone by one `mh undo`.

## Acceptance

- [ ] The banner's count includes intruders and people, read back from disk
- [ ] One click applies all; one `mh undo` brings everything back (test)
