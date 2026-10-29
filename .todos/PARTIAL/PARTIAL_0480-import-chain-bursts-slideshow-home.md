# 0480 — Import chain: copies before tags, the import's bursts, the new event's slideshow, the home page (rest of 0478)

- **Priority**: High
- **Batch**: phone
- **Depends**: —
- **Files**: `src/media_hygiene/cli/templates/mh_phone.ps1.j2`, `src/media_hygiene/services/launcher_phone_end.py`, `src/media_hygiene/review/`, `src/media_hygiene/cli/cmd_slideshow.py`, `src/media_hygiene/review/templates/` (home page)

## Why

0478 (PARTIAL) quarantines the import's exact copies. The maintainer's goal stays « hop import,
hop diaporama », totally clean. Decisions of 2026-10-29 (0478) apply; what remains, in order:

1. `copies` right after the audit, **before** tags (its own step line in `mh_phone.ps1.j2`):
   the AI model never describes a file then set aside. (Order decided by the maintainer: audit →
   duplicates → bursts → tags/places/event.)
2. The burst review page opens on the **import's bursts only**, while tags, places and the
   event name run in the background; no burst → no page.
3. The end line offers the slideshow of the **new event only** (a `slideshow` option for a
   list/period of files).
4. The same chain on the home page, followed live; a chain stopped halfway offered again from the
   next step; steps switched on/off from the list (saved in `[imports] then`, read back);
   the period buttons (*Today · This week · This month · All*).

## Acceptance

As 0478: a synthetic import with 2 copies + 1 burst → copies quarantined before tags run, the
burst page lists that burst only, the slideshow offered plays the new photos only.

## Status — PARTIAL (2026-10-29)

- ✅ 1. Copies before tags: `[imports] then` order is now audit → copies → bursts → tags →
  places; `mh.ps1` runs `phone-end --copies` right after the audit (*🧹 N copies among the
  new files set aside* + undo line); the end line is *✨ All done: N new photos and videos*.
- ✅ 2. Import's bursts only: new step `bursts`; `review --imported <folder> --since <period>`
  (hidden) keeps the series holding a new shot, decided in `import-bursts.json` (the
  library's `decisions.json` untouched). `mh` starts it detached (like the home page) while
  tags/places run; after them, *Done on the burst page? Press Enter*, the container is
  stopped (choices already saved) and `clean --decisions import-bursts.json` applies them
  (journal, byte compare, undo). No series: the container ends, no page, no clean.
- ✅ 3. `slideshow --folder X --since <period>`: the new event only; `phone-end` and the TV
  answer use it.
- ❌ 4. Home page chain (live follow, resume halfway, toggles saved to `[imports] then`,
  period buttons). **Reason:** a new home-page panel + API + tomlkit writer: a lot of its
  own; refiled as 0481.
- Maintainer: step 41 of `mh-measure.ps1`.
