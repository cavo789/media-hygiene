# 0509 — Intruder files: the report and the home page lead to the page that sets them aside, with a cautious hint per extension

- **Priority**: Medium
- **Batch**: intruders
- **Depends**: —
- **Files**: `src/media_hygiene/report/templates/_intruders.html.j2`, `src/media_hygiene/scan/intruders.py`, `src/media_hygiene/review/intruders_views.py`, `src/media_hygiene/review/templates/intruders_review.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/clean/15-intruder-files.md`, `documentation/fr/clean/15-intruder-files.md`

## Reported (maintainer, 2026-10-30)

The report's "Intruder files" section lists, per extension, e.g. `.ithmb · 262 files · 783.8 MB`,
`.7z · 1 file · 574 MB`, `.mp3`, `.ppt`, `.zip`, `.mepx`, `.mpo`, `.mta`, `.js`, `.htm`… The
maintainer asked: how does an ordinary Windows Explorer user delete every `.ithmb` in one go?
Explorer has no way to do it. And what is a `.ithmb`? (looked up online: iPod/iPhone photo
thumbnail cache, safe to delete). Could the tool say "safe / not safe", without ever advising a
risky delete (a `.zip` is not safe unless its content is known to be extracted elsewhere)?
Should there be a feature to delete these files?

## What exists already (read in the code, 2026-10-30)

- The feature exists: `mh review --intruders` (step `review-intruders`,
  `menu_catalog_clean_more.py`; doc `clean/15-intruder-files`): ticks per extension and/or
  folder, then sets the files **aside in the quarantine** (undoable), protected and backup
  folders left out. This is exactly "all the `.ithmb` in one step".
- The gap is discoverability: `report/templates/_intruders.html.j2` says "Nothing is moved: a
  document may matter. intruders.csv lists every file." and never names that page or command.
  The user reading the report concludes there is no way.

- `mh audit` already warns: `cli/audit_intruders.py` prints "🧹 N files that are not photos or
  videos (ithmb, 7z, mp3, …) take X…; 'review --intruders' picks those to set aside", and when
  nothing else is left the 👉 What next line is that page. The console is covered.
- The home page says nothing: the action "Set the intruder files aside" is listed among the
  optional Clean steps, with no count; the Clean badge (`stage_badge`, `home_stage_lines.py`)
  counts only extra copies. A user of the page only learns about intruders by opening a report.

## Challenge (the answers kept)

1. **No new delete feature.** A second way would duplicate `review --intruders`; and a direct
   delete breaks the project rule that a clean is undoable (quarantine, then `purge`). Keep one
   path: the report points to the page.
2. **A hint, never a verdict.** The tool cannot know whether a `.zip` was extracted or a `.doc`
   is the only copy. So three wordings only, from a short vetted table in `scan/intruders.py`:
   - *cache, rebuilt by the device or app* — e.g. `.ithmb` (iPod/iPhone thumbnails), browser
     page leftovers (`.js`, `.css` next to a saved `.htm`?) — to check one by one before adding;
   - *keep unless you have it elsewhere* — archives (`.zip`, `.7z`, `.rar`), documents (`.doc`,
     `.ppt`, `.xls`, `.pdf`), audio, project files (`.psd`, `.pdn`, `.mepx`?);
   - *unknown* — everything else, the default: no advice.
   Each entry of the table must be checked against a source before landing (rule: no unchecked
   fact about a third-party format). Even "cache" stays "set aside", never "delete".
3. **`.mpo` is probably not an intruder:** MPO (Multi Picture Object) is a 3D/multi-frame JPEG
   from some cameras (Fujifilm, Nintendo 3DS); Pillow opens it. To verify, then likely add it to
   the photo extensions (a separate fix, its own test) rather than offer to set it aside.
4. **`.mta`, `.mepx`, `.alb`: unknown to us** — leave them "unknown" until checked.

## To do

1. Report: under "Intruder files", one line with the command to paste (`mh review
   --intruders`, Windows-first, read-only 🔒 wording as elsewhere) and, in the served shell,
   a link to the page.
2. Home page: moved to TODO 0515 (an *Intruder files* tile in *Where you are*, weight + one
   click to the page).
3. The hint table (point 2) in `scan/intruders.py`; shown next to each extension in the report
   and on the `review --intruders` page (a muted word, not a colour that suggests "go").
   Should it be a setting? Proposed: no (`few-settings`): a constant; the user's own judgment
   is the tick box.
4. Check `.mpo` (point 3): if Pillow decodes it, make it a photo; test with a synthetic MPO.
5. Tests: the report names the command; each hint wording; an unknown extension gets none.
6. Docs EN + FR `clean/15-intruder-files.md`: the hint and why it never says "delete".
   `docs_screenshots` should then run (report and intruders page change) — not run by the TODO.
