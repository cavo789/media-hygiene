# 0708 — Oversized templates split when a change touches them

- **Priority**: Low
- **Batch**: templates
- **Depends**: —
- **Files**: `tests/unit/test_page_frame.py`, `src/media_hygiene/review/templates/`, `src/media_hygiene/search/templates/`

Filed 2026-11-11 by the review of `feedback-2026-11-10-iterate.md` (0668), decided by the maintainer.

## Context

0668 split the places page and listed 7 templates over 440 lines in `OVERSIZED_TEMPLATES` (may only shrink): home_run.js 603, home_parts.css 547, search.js 540, review.html 501, config.toml 501, mh_phone.ps1 475, search.html 448. Decided: split each when a TODO touches it, not as 7 TODOs.

## Acceptance

- [x] A rule line in `.claude/rules/` (or the photo-picking skill): a TODO touching one of them splits it first (rendered output identical, as 0668 proved)
- [ ] Each split removes its entry from `OVERSIZED_TEMPLATES`

## Status (2026-11-12): PARTIAL

- [x] The rule line is in `.claude/rules/workflow.md` (split first, own step, then drop the entry).
- [ ] Left: the 7 splits themselves, each when a TODO touches its template (none did in this run).
