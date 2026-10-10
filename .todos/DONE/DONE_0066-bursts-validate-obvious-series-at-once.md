# 0066 — Bursts: obvious or to look at, and one click validates the obvious ones

- **Priority**: High — thousands of series on the real collection (≈ 4,000)
- **Batch**: review-bursts
- **Depends**: —
- **Files**: `src/media_hygiene/review/views.py`, `src/media_hygiene/review/session.py`, `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/templates/review_choices.js.j2`, `src/media_hygiene/review/templates/review_tree.js.j2`, `src/media_hygiene/review/templates/review_order.js.j2`, `src/media_hygiene/config/review_settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/cli/cmd_review.py`, `documentation/en/clean/10-review-bursts.md`, `documentation/fr/clean/10-review-bursts.md`

## Context

Filed from the 2026-10-10 usability review (human-work axis). Reviewing ~4,000 series one
by one is not realistic, even at the measured pace. Today the proposal is sharpness only
(`[review] propose_aside_below = 0.35`) and a folder can be validated at once, but nothing
says "validate every obvious series, show me only the doubtful ones".

## Proposal

- Each series gets a confidence: **obvious** (a clear sharpness gap, or the near-identical
  shots of the richer-proposals TODO) or **to look at** (shots that really differ:
  framing, subject). Thresholds in `[review]`.
- Page: a button and a key (`V`) "Validate the N obvious series (M shots set aside)" with
  a confirmation giving the figures; one `Z` takes the whole batch back. A filter "Only
  the series to look at", next to "Only the series still to see".
- Console at start: `4,000 series: 3,100 obvious (one click), 900 to look at`.
- Unchanged safety: shots go to the quarantine with `clean --decisions`, `undo` brings
  them back; series never seen stay whole.

## Acceptance

- The batch is one write of `decisions.json`, read back from disk before the page shows
  it (proof, not promise). Unit tests on the confidence; integration test on the batch +
  undo; docs and screenshots en and fr.
