# 0310 — Audit report: a status per chapter, 5 examples, a button that opens the review

- **Priority**: Medium
- **Batch**: report
- **Depends**: 0309
- **Files**: `src/media_hygiene/report/templates/report.html.j2`, `src/media_hygiene/report/templates/_similar.html.j2`, `src/media_hygiene/report/templates/_bursts.html.j2`, `src/media_hygiene/report/templates/_toc.html.j2`, `src/media_hygiene/report/templates/_actions.html.j2`, `src/media_hygiene/report/similar_views.py`, `src/media_hygiene/constants.py`, `src/media_hygiene/config/`, `src/media_hygiene/review/home_step.py`, `src/media_hygiene/review/report_files.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/clean/04-html-report.md`, `documentation/fr/clean/04-html-report.md`, `tests/unit/test_reports.py`, `tests/unit/test_similar.py`

## Context

The maintainer, 2026-10-23: the audit report is "what was found". It does not need to show
every near duplicate or burst series ("it is only a report"), but it should let the reader
act at once: "I see the report, OK let's go", from the report itself.

Checked in the code: the report shows every near duplicate and up to 200 burst series
(`Sizes.MAX_BURSTS_IN_REPORT`); `near.html` and `plan.csv` already hold the full lists. The
home page serves the reports under `/reports/` (`review/report_files.py`) and already starts
a menu step from a page (`POST /api/step`, `review/home_step.py`: the server ends, `mh` runs
the command); `review-near` and `review` are in the menu catalog. The report already has a
"What you can do" block with copy buttons (`_actions.html.j2`).

## What to do

1. **A status badge on every chapter** (title and table of contents):
   - 🧹 **`clean` takes care of it**: exact copies, broken files, orphan sidecars;
   - 👀 **Yours to decide**: near duplicates, re-encoded videos;
   - ℹ️ **For your information, nothing to do**: burst series (folded by default, last).
2. **A few examples, not the whole list**: per chapter, a count line (groups, space, sure /
   to check) and the 5 largest examples; a link to `near.html` and the CSV for the full list.
   Propose the 5 as a setting (`[report] examples`, to discuss in the feedback).
3. **A ▶ button per chapter to decide**: "Decide in the browser" (`review --near`), "Sort the
   bursts" (`review`). When the report is served by the home page (same origin), the button
   posts the menu step (`/api/step`) and the review opens; opened from the disk (`file://`)
   or from `mh reports`, no step can run: the button is replaced by the command to copy
   (the one-liner, as `_actions.html.j2` does). Detect it from the page (the home page's
   API answering), never guess. The report stays a static file: no new server route
   unless the existing step API is not enough (then say why in the feedback).

## Done when

- Each chapter shows its badge; bursts are folded and last.
- 5 examples per chapter, a count line and the full-list links.
- The button starts `review --near` from the home page (a test of the request it sends and
  of the fallback to the command when the API is not there).
- `i18n_update` run, French translated; documentation in both languages; say that
  `docs_screenshots` should run.

## Gain (estimated)

The reader reaches the review from the report in one click instead of copying a command
into PowerShell; the audit report writes 5 thumbnails per chapter instead of every near
duplicate and up to 200 bursts. The time saved writing the report is not measured: measure
it on the demo tree before and after (`demo`, then time the report step).
