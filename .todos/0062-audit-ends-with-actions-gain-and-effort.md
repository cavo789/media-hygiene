# 0062 — The audit ends with what you can do: gain and effort per action

- **Priority**: Medium
- **Batch**: guidance
- **Depends**: 0061
- **Files**: `src/media_hygiene/console/tables.py`, `src/media_hygiene/services/audit.py`, `src/media_hygiene/cli/flows.py`, `src/media_hygiene/report/templates/`, `src/media_hygiene/report/views.py`, `documentation/en/start/01-first-audit.md`, `documentation/fr/start/01-first-audit.md`

## Context

Filed from the 2026-10-10 usability review. The audit shows a summary table plus an
inventory table; the user must infer what to do and how long it takes. On a real
collection (≈ 4,000 burst series, > 500 near duplicates) the numbers frighten rather than
guide, and nothing says that reviewing bursts is optional.

## Proposal

- Below the summary, at most three action lines, each with gain and effort:
  - ✅ `12 identical copies, 3.4 MB: no risk, one command`
  - 👀 `1 near duplicate: one group to look at (~1 min)`
  - 🎞 `3 burst series: optional, ~2 min in review — series not reviewed are kept`
- Effort from a fixed estimate per group / series (configurable later; the review page's
  measured pace is the reference).
- The *Inventory* table leaves the default audit output (still in `inventory`, and with
  `--verbosity verbose`).
- The HTML report opens with the same three actions in a box, each with a "copy the
  command" button (the command of the full-command TODO, 0059 when done).

## Acceptance

- Captures en and fr regenerated; the box is in `report.html`; tests on the effort lines.
