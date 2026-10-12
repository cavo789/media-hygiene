# 0122 — `review` accepts `--exclude-name` and `--ext`, like `audit`

- **Priority**: Low
- **Batch**: review
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_review.py`, `src/media_hygiene/cli/review_options.py`, `src/media_hygiene/cli/scan_options.py`, `documentation/en/commands/review.md`, `documentation/fr/commands/review.md`

## Context

DONE 0043 left `review` with `--exclude` but without `--exclude-name` nor `--ext`, although
`review` runs the same audit first. Decided in review 0056 (2026-10-12): add them, for
consistency (a user who audits with `--ext photo` expects `review --ext photo` to see the
same files).

## What to do

- Reuse the options of `scan_options.py` (as `audit` does) in `cmd_review.py`, into the same
  folder/scan settings layer.
- Docs: the options table and the `--help` capture of `commands/review.md` (en + fr;
  `docs_screenshots` refreshes the capture).

## Acceptance

- `review --ext photo` and `review --exclude-name Thumbnails` reach the audit's settings (test,
  as for `audit`).
