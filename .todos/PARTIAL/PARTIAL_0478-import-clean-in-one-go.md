# 0478 — Import and be clean in one go: duplicates, bursts, the new event's slideshow (rest of 0475)

- **Priority**: High
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/services/launcher_phone_end.py`, `src/media_hygiene/config/import_settings.py`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/services/clean.py`, `src/media_hygiene/review/`, `src/media_hygiene/review/templates/` (home page)

## Why

The maintainer, 2026-10-29: « hop import, hop diaporama »: import today's photos from the phone
and, with nothing else to do, be totally clean, then get the slideshow offered (not forced).
0475 (PARTIAL) runs audit → 🤖 tags → places → « slideshow ready ». What remains:

## Decided (2026-10-29, the maintainer)

1. **Exact duplicates** of the new files (byte-identical, e.g. the same photo twice via WhatsApp):
   quarantined automatically (the usual `clean` path: journal, byte compare, `undo` puts them back).
2. **Bursts** of the new files: the existing burst review page opens on the import's bursts only;
   the user picks as usual. While it is open, tags, places and the event name run in the
   background; no burst → the page does not open.
3. The end line: « ✨ All done: 42 imported, 3 copies set aside, 2 bursts reviewed. 📺 Your
   slideshow *Promenade à Liège* is ready: send it to the TV? » — the slideshow of the **new
   event only** (today it shows the whole phone folder).
4. Rest of 0475: the same chain on the home page (each step followed live); a chain stopped
   halfway (Ctrl+C, PC asleep) is offered again by the next `mh` from the next step; steps
   switched on/off from the list itself, saved in `[imports] then` (read back from disk).
5. Rest of 0476: the period buttons (*Today · This week · This month · All*) on the home page.

## Acceptance

- Synthetic import with 2 exact copies + 1 burst: the copies are in quarantine (journal), `undo`
  restores them; the burst page lists that burst only; the end line counts both.
- The slideshow offered plays the new event's photos only.
- A step of `tests/measure/mh-measure.ps1` times the whole chain (maintainer's PC).

## Status — PARTIAL (2026-10-29)

### Done
- Decided 1, exact duplicates: new step `copies` of `[imports] then` (on by default, last in the
  list), run by `phone-end`: an audit, the plan cut to the new files (`services/import_copies.py`:
  only new files ever go; a group whose policy kept a new file keeps the library's older copy
  instead), then `CleanService.execute` (journal, byte compare; `mh undo` restores). No quarantine
  or journal mount: one warning, the chain goes on. Tests: `tests/unit/test_import_copies_plan.py`,
  `tests/integration/test_import_copies.py` (2 copies set aside, undo restores them).
- Decided 3, part: the end line « ✨ All done: N imported, K copies set aside. » + the undo line,
  before the slideshow line. Docs en+fr (`commands/import.md`), config template, French .po.
- Measure step 40 of `tests/measure/mh-measure.ps1` (whole chain timed, end line, undo).

### Not done
- Decided 2: the burst page opened on the import's bursts only, with tags/places/name running in
  the background; the end line's « N bursts reviewed ».
  **Reason:** out of this lot's size (review page filter + background orchestration from mh.ps1).
- Decided 3: the slideshow of the new event only (`slideshow` has no `--since`/files option yet;
  the line still shows the whole phone folder).
  **Reason:** needs a new slideshow selection (files of the period); out of this lot's size.
- Decided 4 and 5 (rest of 0475/0476): home-page chain followed live, resume after interruption,
  toggles from the list saved in `[imports] then`, period buttons on the home page.
  **Reason:** out of this lot's size.
- `copies` runs after `tags` (it lives in `phone-end`): the 🤖 model also describes the copies
  set aside. Moving it right after the audit needs its own step line in `mh_phone.ps1.j2`.
