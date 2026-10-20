# 0273 — The HTML reports wear the home page's look

- **Priority**: Medium — asked by the maintainer (2026-10-20): "every web page the tool creates"
- **Batch**: report
- **Depends**: 0268
- **Files**: `src/media_hygiene/report/templates/base.html.j2`, `src/media_hygiene/report/templates/index.html.j2`, `src/media_hygiene/report/environment.py`, `src/media_hygiene/report/writer.py`, `src/media_hygiene/report/classify_writer.py`, `src/media_hygiene/report/index_page.py`, `src/media_hygiene/review/templates/theme.css.j2`, `src/media_hygiene/assets/theme/` (new), `tests/unit/test_report_look.py` (new), `documentation/en/images/`, `documentation/fr/images/`

## Context

The reports (`report/templates/`: the audit and clean report, one page per folder pair, the
near duplicates, the classify proposal and its years, `index.html`) are self-contained files. A
user opens them from disk (`mh open`, a `file://` address) or through the home page under
`/reports/`. Their look is the GitHub-like tokens inlined in `base.html.j2` (read on
2026-10-20). 0268 gives the served pages the avonture.be look; the maintainer wants every page
of the tool alike.

## What to do

1. **The tokens in one file both template environments reach.** 0268's `theme.css.j2` sits under
   `review/templates`, while the reports use their own environment (`report/environment.py`).
   Move the tokens to `src/media_hygiene/assets/theme/` and inline them in both, so the colours
   are written once.
2. **`base.html.j2`.**
   - The `--mk-*` and `--mh-*` tokens, light and dark, following the OS. A report has no switch:
     it is a file.
   - A header with "Media Hygiene", the avatar, the report's kind and date, and a
     "Documentation" link (both languages) to the chapter that explains this report (0265's
     catalog `doc`).
   - The tables, cards and previews keep their layout.
3. **What a file can load.** The report must stay complete when opened from disk.
   - The avatar is inlined (a `data:` URI, about 30 KB per report, estimated from its 21.8 KB
     WebP).
   - The fonts: see decision 1.

## Decisions (proposed defaults, for `/todo:iterate` to ask first)

1. **Fonts in the reports.** Proposed: the system fonts (Segoe UI and Cascadia Mono on Windows).
   The colours, the header and the meerkat carry the look. To check: Chrome may refuse an
   `@font-face` loaded from a `file://` page (cross-origin rules for local files); inlining
   the three families would add about 400 KB to each report (estimated, base64 of about
   300 KB).
2. **The previews folder** stays where it is: nothing changes in what a report writes next to
   itself.

## Acceptance

- `tests/unit/test_report_look.py`: each kind of report renders the header and both themes' tokens;
  its doc link leads to its chapter in both languages; the HTML names no outside URL.
- A report opened from disk shows its avatar, with no request to the network.
- The report captures (`report-*.webp`, `index.webp`, `pair.webp`, `clean-report.webp`,
  `classify-*.webp`) go stale: say that `docs_screenshots` should run.

## Gain (counted)

Six kinds of report (counted from the templates: the audit or clean report, the folder pair, the
near duplicates, the classify proposal, its years, the index) in the look of the pages that open
them. The help for each report is a click away.

## Decided (2026-10-20)

- Decision 1: **system fonts** (Segoe UI and Cascadia Mono on Windows); the colours, the header
  and the meerkat carry the look. No inlined font families. By the maintainer, at the start of
  `/todo:iterate`.
