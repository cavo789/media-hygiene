# 0288 — Burst review opened from home: an *Apply now* button runs `clean --decisions`

- **Priority**: medium
- **Batch**: home
- **Depends**: 0287
- **Files**: src/media_hygiene/review/app.py, src/media_hygiene/review/near_app.py, src/media_hygiene/review/templates/review.html.j2, src/media_hygiene/review/templates/near_review.html.j2, src/media_hygiene/search/apply_api.py (reuse), src/media_hygiene/cli/cmd_review.py, src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po, documentation/en|fr/commands/review.md, documentation/en|fr/clean/10-review-bursts.md

## Context

After choosing in the burst review page ("Tri des rafales"), the maintainer did not know how to
apply (2026-10-21): Ctrl+C in PowerShell (twice, see 0287), `mh clean --decisions`, then `mh`
again. The intended path exists but takes three moves: "⌂ Back to the home page", then the home
step "Apply your choices" (`clean --tier near --decisions`, `menu_catalog_clean.py`).
`browse` already has the one-click version (0243, `search/apply_api.py`, `POST /api/apply`): it
ends the page with the exit code of the home step that applies, `mh` runs it with its usual
question, then opens home again. No new path in `mh`.

## Acceptance

- [ ] Opened from home (the signal "⌂ Back to the home page" uses) with at least one shot or
      series set aside in `decisions.json`: an *Apply now* button near the saved-decisions panel;
      its `POST` ends the page with the "Apply your choices" step's code. Shared with `browse`
      (move `apply_api` to `review/` if both use it), not copied.
- [ ] Opened by `mh review` directly: no button, the 👉 next line stays. Nothing set aside: no
      button (or disabled, with why).
- [ ] Same on the near-duplicates page (`near_review`), or said why not.
- [ ] Integration tests: from home with a choice → button and step code; directly → none;
      nothing chosen → none.
- [ ] Strings via `_()`, French translated; docs en + fr; `docs_screenshots` to run.

## Gain (estimated)

From the burst page to the quarantine: one click + the console's confirmation, instead of
back home, find the step, click (3 moves) — or, as happened, two Ctrl+C and two typed commands.
