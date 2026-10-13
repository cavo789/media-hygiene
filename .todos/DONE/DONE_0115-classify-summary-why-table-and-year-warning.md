# 0115 — `classify` summary: translated reasons, a titled category list, a short warning under `--year`

- **Priority**: Medium — read on the maintainer's first real `--year` run
- **Batch**: classify
- **Depends**: —
- **Files**: `src/media_hygiene/classify/engine.py`, `src/media_hygiene/console/classify_view.py`, `src/media_hygiene/classify/names.py`, `src/media_hygiene/cli/classify_flow.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/sort/`, `documentation/fr/sort/`, `documentation/en/commands/classify.md`, `documentation/fr/commands/classify.md`

## Context

`mh classify --year 2015` on the real collection (2026-10-12, review 0056) printed, under
`--locale fr`:

```text
Pourquoi
│ Dossiers existants                               │ 1.758 │
│ undated                                          │ 1.342 │
│ Sujet                                            │   200 │
│ no-signal                                        │    26 │
│ …                                                │       │
│   iPad_Manon                                     │ 1.834 │
│   Photos Chloé                                   │   367 │
…
⚠️  Règles qui n'ont rien décidé : Films et séries, Week-end à Dinant 2020, … (55 names)
```

Three defects:

1. `_reasons_table` prints `proposal.reason.value` when no rule decided: the raw codes
   `undated`, `no-signal` (and any other `Reason` value) reach the user untranslated.
2. The indented rows are the ten most frequent **categories**, under no title: the maintainer
   read them as folders without knowing why they were there.
3. With `--year`, every rule written for another year is listed as "decided nothing": 55 names
   of pure noise. Decided in review (0056 Part 3): the list stays for a run without `--year`.

## What to do

1. A translated name for every `Reason` value in `classify/names.py` (next to `band_name`):
   "Sans date" / "Undated", "Aucun indice" / "No signal", … — used by the *Why* table. Check
   whether the workbook's *Reason* column already has such names and share them.
2. Split the categories from the reasons: a second table (or a titled section) "Catégories les
   plus remplies" / "Largest categories", so the indented rows explain themselves.
3. With `--year` (any year range), replace the list by one line:
   "55 règles n'ont rien décidé en 2015 : normal pour celles écrites pour d'autres années." —
   no names, no tip; the workbook's summary sheet keeps the full list as today. Without
   `--year`, unchanged.
4. Undated files under `--year` (decided 2026-10-13): the same run proposed 1,342 files with no
   EXIF date (band "Sans date") because their year is guessed from the file's modification date
   (`iPad_Manon`, copied in 2015). They all go to `undated_layout` whatever the year, so in a
   `--year` run they only swell the figures. With `--year`, leave out every proposal whose
   dating is a guess from the modification date (check `Dating` for how that source is
   recorded; `_in_years` in `engine.py`), and say it in one line:
   "1 342 fichiers sans date : proposés par un classify sans --year." Without `--year`,
   unchanged. The workbook of a `--year` run then holds no undated row; check the carry-over
   keeps undated edits of an earlier full run.
5. Console blocks of the docs that show this summary (en + fr), `i18n_update`, translations.

## Explicit NON-goals

- The subject lines above the summary (0114).

## Acceptance

- No raw `Reason` code in the console in either language (a test over every `Reason` value).
- The category rows sit under their own title.
- Under `--year`, one line instead of the list; without it, the list as today. Tests for both.
- Under `--year`, no undated file is proposed and one line counts them (test).
