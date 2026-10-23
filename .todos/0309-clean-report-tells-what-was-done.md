# 0309 — The clean report tells what was done, not what could be done

- **Priority**: High
- **Batch**: report
- **Depends**: —
- **Files**: `src/media_hygiene/report/templates/report.html.j2`, `src/media_hygiene/report/templates/_similar.html.j2`, `src/media_hygiene/report/templates/_bursts.html.j2`, `src/media_hygiene/report/templates/_toc.html.j2`, `src/media_hygiene/report/views.py`, `src/media_hygiene/report/summary.py`, `src/media_hygiene/services/clean.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/clean/08-clean.md`, `documentation/fr/clean/08-clean.md`, `documentation/en/clean/04-html-report.md`, `documentation/fr/clean/04-html-report.md`, `tests/unit/test_reports.py`

## Context

The maintainer, 2026-10-23: a report is "what has been done" (the past). The "Clean report"
shows the chapters "Near duplicates" and "Burst series" exactly as the audit report does, so
it reads as a to-do list. The same chapters in both reports add to the confusion.

Checked in the code: `_similar.html.j2` and `_bursts.html.j2` never test `is_clean`.
A clean report labels a near-duplicate copy "📦 to the quarantine with --tier near" (future
tense) whether or not `--tier near` was given. `CleanMode` (`services/clean.py`) knows
`near` and `bursts` (`--decisions`), but the report does not show which of them ran (to check:
whether `ReportRecord`/`ReportSummary` carries them).

## What to do

The clean report answers one question, in two clearly separated blocks:

```
✅ What this clean did
   🧬 Exact copies removed .............. 1,234 files · 8.2 GB
   🪞 Near duplicates moved to the quarantine   (only with --tier near)
   📸 Burst shots set aside .............       (only with --decisions)
   💔 Broken files moved to the quarantine
   ↩️ To undo it all: mh undo <run>

⏸️ Not touched by this clean (decide later, if you want)
   🪞 312 near duplicates  → mh review --near
   📸 45 burst series      → mh review
   (details in the audit report of <date>, a link)
```

- Past tense everywhere in the first block, from what the journal recorded (a save is
  proven by reading it back: count what the journal says was done, not what the plan asked).
- Near duplicates, re-encoded videos and bursts appear in the clean report **only** as what
  was done to them (the files moved, with their thumbnails), or as **one line** in the
  "Not touched" block, which points to the audit report (the latest one of the same folders)
  and to the `review` command. No thumbnails of untouched groups, no future tense.
- Carry `CleanMode.near` / `CleanMode.bursts` into the summary (`summary.json`, a new
  optional field with a default, so the reports of older runs still load:
  `tests/fixtures/0.2.0/`).
- The table of contents follows the two blocks.
- The audit report is not changed here (0310).

## Done when

- A clean without `--tier near` shows no near-duplicate thumbnails, only the "Not touched" line.
- A clean with `--tier near` lists the near duplicates moved, in the past tense.
- Tests for both cases, and for bursts with and without `--decisions`.
- `i18n_update` run, French translated; the report pages of the documentation updated in
  both languages; say that `docs_screenshots` should run (never run it unasked).

## Gain (estimated)

From the templates: "what did this clean do?" is answered by the first block alone instead
of reading every chapter and interpreting the `--tier near` mentions; the clean report loses
the thumbnails of the untouched near duplicates and bursts (up to 200 series today,
`MAX_BURSTS_IN_REPORT`), so it is shorter and quicker to write. Not measured.
