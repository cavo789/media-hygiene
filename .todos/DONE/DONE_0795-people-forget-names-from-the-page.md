# 0795 — people --forget --names from the page

- **Priority**: Medium
- **Batch**: people
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_people.py`, `src/media_hygiene/review/`

Follows PARTIAL 0740 (`.todos/PARTIAL/PARTIAL_0740-left-by-0505-home-run-container-steps-in-a-popup.md`); decided by the maintainer in the review of 2026-11-13 (`.claude/plans/feedback-2026-11-13-iterate.md`).

`people --forget --names`: the page asks which names to forget (confirmation stating the count), deletes them from `config.toml` (tomlkit, comments kept, atomic, `/config/.history/`), reads the file back and shows what was removed. `restore` stays in the mh window (decided).

## Status — DONE (2026-11-13)

- `people --forget --names`: the names of `config.toml` and the faces ignored go without a
  question; read back and shown (*0 names*, *Names removed: …*), the previous file kept in
  `/config/.history/` (`replace_text`); the people files unlinked are copied there first too.
- Home page: *Forget every face and every name* (Privacy, `Risk.FINAL`, inline): its
  confirmation is read from `config.toml` at each state, states the count and lists every name;
  not offered when nobody is named (`cli/home_forget.py`).
- Tests: `test_home_forget.py`, `test_people_names.py` (`--names`), catalog lists updated.
  Docs EN + FR (`commands/people.md`, `commands/home.md`). `docs_screenshots` should run.
