# 0412 — The clean report links the latest audit report of the same folders

- **Priority**: Low
- **Batch**: report
- **Depends**: —
- **Files**: `src/media_hygiene/report/` (the builder), `src/media_hygiene/report/templates/report.html.j2`, `tests/unit/test_clean_done.py`, `documentation/en/clean/08-clean.md`, `documentation/fr/clean/08-clean.md`

## Context

0309 (commit 70b746c) opens a clean report with "What this clean did" and "Not touched by this
clean", which tells the reader to look in *All reports* for the near groups and bursts left.
Maintainer, review of 2026-10-27: link straight to the latest audit report of the same folders.
The builder has no list of the reports today.

## Steps

1. Give the report builder the reports listing (the one `index.html` is made from).
2. Pick the latest audit report whose folders are the clean's; none: keep the *All reports* line.
3. The "Not touched" block links it; test with two audits of different folders.

## Acceptance

- A clean report after an audit of the same folders links that audit's report.
- No such audit: the *All reports* line, as today.
