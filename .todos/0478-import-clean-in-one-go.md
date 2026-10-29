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
