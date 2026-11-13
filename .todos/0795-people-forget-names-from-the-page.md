# 0795 — people --forget --names from the page

- **Priority**: Medium
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_people.py`, `src/media_hygiene/review/`

Follows PARTIAL 0740 (`.todos/PARTIAL/PARTIAL_0740-left-by-0505-home-run-container-steps-in-a-popup.md`); decided by the maintainer in the review of 2026-11-13 (`.claude/plans/feedback-2026-11-13-iterate.md`).

`people --forget --names`: the page asks which names to forget (confirmation stating the count), deletes them from `config.toml` (tomlkit, comments kept, atomic, `/config/.history/`), reads the file back and shows what was removed. `restore` stays in the mh window (decided).
