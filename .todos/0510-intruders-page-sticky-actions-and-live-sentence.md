# 0510 — Intruders page: the buttons in the sticky bar, one live sentence, folders filtered by the extension ticked, Apply now

- **Priority**: High
- **Batch**: intruders
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/intruders_review.html.j2`, `src/media_hygiene/review/templates/intruders_review.js.j2`, `src/media_hygiene/review/intruders_views.py`, `src/media_hygiene/review/intruders_app.py`, `src/media_hygiene/services/intruders_reviewing.py`, `src/media_hygiene/review/apply_api.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/unit/`, `documentation/en/clean/15-intruder-files.md`, `documentation/fr/clean/15-intruder-files.md`

## Reported (maintainer, 2026-10-30)

`mh review --intruders` typed in PowerShell:

1. The page opened "well hidden" (behind the other windows? — ask if unclear).
2. The buttons ("Set the files ticked aside", "Put every intruder file back") are at the
   bottom, after both tables: a long scroll. On `/search` they are at the top. Wanted: in a
   sticky zone at the top.
3. Not understood: `.ithmb` ticked (262 files, 783.8 MB) plus one folder ticked — are the
   `.ithmb` of that folder only set aside, or every `.ithmb` plus every intruder of that
   folder? The side text says it (intersection: "a file must match one ticked extension and
   lie in one ticked folder") but nobody reads it. Wanted: explicit without reading.

Follow-up the same day: "I have no idea where these files are": ticking `.ithmb` should
filter the folder list to the folders that hold some (point 3 below, confirmed). And an
**Apply** button "as everywhere else" is missing.

## Today (read, 2026-10-30)

- `intruders_review.html.j2`: the page already has a `{% block bar %}` (sticky) holding only
  `#summary` and `#status`; the `.actions` div sits in `<main>` after the tables.
- Ticks combine as an intersection (extension AND folder); either alone = all of it.
- The button only records the choice in the decisions file (🔒 nothing moves); `clean
  --decisions` then quarantines — the button label "Set aside" does not say so either.
- *Apply now* (`review/apply_api.py`, `ApplyingApp`) is offered by the pairs, near and
  unwanted reviews (`ApplyOffer(start.apply, …)` in `*_reviewing.py`);
  `intruders_reviewing.py` builds no `ApplyOffer`: the intruders page has no Apply.

## To do

1. Move both buttons into the sticky bar, at the place `/search`'s bar puts its actions
   (same look as the `pick_*` bar: skill `photo-picking-pages` for placement, though this
   page has no tiles).
2. **One live sentence in the bar** — the answer, computed from the ticks, before clicking:
   - nothing ticked: "Tick an extension or a folder." (button disabled);
   - extensions only: "262 .ithmb files (783.8 MB), in every folder";
   - folders only: "every intruder file of D:\Photos\2010 (41 files, 12 MB)";
   - both: "the .ithmb files of D:\Photos\2010 only (12 files, 40 MB)".
   The button carries the count: "Set these 12 files aside". The counts come from the
   files the page already has (no new disk read).
3. While an extension is ticked, the folder table **lists only the folders holding that
   extension** (hidden, not dimmed: the user wants to see where they are), each with the
   count and size of that extension; same the other way (a folder ticked → only its
   extensions). A folder ticked then filtered out stays ticked and is said in the
   sentence, never silently dropped. Unticking everything shows all rows again.
4. Shorten the side text to what the sentence does not say (what an intruder is, protected
   folders left out, the clean step after).
5. **Apply now**, as on the other reviews: `intruders_reviewing.py` offers `ApplyOffer`
   (pending = some files set aside), so the page opened from home shows the same Apply
   button at the same place (`clean --decisions` through `apply_relay`, its usual
   question). Opened by its command alone, the same behaviour as the other reviews (no
   button; the bar shows the next command, copied). Say "nothing moves until Apply".
6. Point 1 of the report (the page opened behind): check how `mh` opens the browser for a
   typed page vs from home (`Start-Process` in a job); if it can be brought to front
   without a run-time compile (Avast), do it; else file a follow-up.
7. Tests: Apply offered once something is set aside, not before; the filtered folder
   list (and a ticked folder kept when filtered out); the sentence for the four cases (EN + FR, plural forms); the counts per folder
   with an extension ticked; the button disabled with nothing ticked.
8. Docs EN + FR `clean/15-intruder-files.md`; `docs_screenshots` should then run (page
   changes) — not run by the TODO.

## Where the user gains

Before: scroll past both tables to find the button, and guess what a mix of ticks does.
After: the button is always in view and says, in numbers, exactly which files go.
