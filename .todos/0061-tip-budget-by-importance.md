# 0061 — A tip budget: one What next and two tips at most, by importance

- **Priority**: High — the first audit prints 7 tips and buries the one that matters
- **Batch**: guidance
- **Depends**: —
- **Files**: `src/media_hygiene/console/output.py`, `src/media_hygiene/cli/flows.py`, `src/media_hygiene/cli/cmd_audit.py`, `src/media_hygiene/cli/cmd_clean.py`, `src/media_hygiene/cli/cmd_review.py`, the other callers of `Output.tip()`

## Context

Filed from the 2026-10-10 usability review. The captured first audit
(`documentation/en/start/01-first-audit.md`, `audit-photos.txt`) ends with seven 💡 lines
(reports mount, Czkawka, `--prefer`, near duplicates, review, cache, TZ) then the 👉 line;
there are 69 `tip()` calls in `src/`. Users who never read docs stop reading after two.

## Proposal

- `Output` collects tips during a command instead of printing them at once; each tip gets
  a kind, in this order: safety (undo line, read-only) › next step › setup (cache,
  `/reports`, TZ) › discovery (Czkawka, `--prefer`, review, near).
- At the end: the 👉 line, then the two most important tips. Setup tips are merged into
  one line: `⚙ To set once: -v media-hygiene-cache:/cache (faster audits), -e TZ=…`.
- The rest only with `--verbosity verbose` (one closing line says how many were hidden).
- Safety lines (undo/purge after clean) are never cut.

## Acceptance

- `audit-photos.txt` shows at most three advice lines; clean still shows its undo line.
- Unit tests on ordering, merging and cutting; captures regenerated (en and fr).
