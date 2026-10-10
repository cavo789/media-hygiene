# 0069 — Near duplicates: decide in the browser, per group or per folder pair

- **Priority**: High
- **Batch**: near
- **Depends**: 0068
- **Files**: `src/media_hygiene/review/` (new near view: `near_app.py`, `near_session.py`, templates), `src/media_hygiene/report/decisions.py`, `src/media_hygiene/services/near_checks.py`, `src/media_hygiene/services/clean.py`, `src/media_hygiene/cli/cmd_review.py`, `src/media_hygiene/cli/review_options.py`, `documentation/en/clean/11-near-duplicates.md`, `documentation/fr/clean/11-near-duplicates.md`, `documentation/en/clean/12-decide-pair-by-pair.md`, `documentation/fr/clean/12-decide-pair-by-pair.md`

## Context

Filed from the 2026-10-10 usability review. Near duplicates are all or nothing: a user who
disagrees with five groups out of 500 can only skip the tier or undo after the fact. Exact
duplicates already have folder pairs as the main decision unit (DONE 0014) and per-pair
decisions in `decisions.json` (DONE 0017).

## Proposal

- Reuse the `review` server and keyboard (`review --near`, or a tab of the same page): per
  group `→` as planned, `W` keep the other version, `L` leave alone; the groups to check
  first (levels of 0068).
- **Decide once per folder pair**: `312 groups between WhatsApp Images and DCIM: as
  planned?` — one key for all of them, still reversible per group.
- Choices saved at each key in the same `decisions.json` (new `near` key, next to `pairs`
  and `bursts`); `clean --decisions --tier near` applies them with the usual checks:
  stale group → file refused, protected folder never moved.
- Sort orders shared with the gain TODO (largest space first).

## Acceptance

- Integration test: decide, `clean --decisions --tier near`, `undo`.
- Decisions read back from disk before the page shows them; docs and screenshots en/fr.
