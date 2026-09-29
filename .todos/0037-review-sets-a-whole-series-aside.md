# 0037 — `review`: set a whole burst series aside (none of its shots is worth keeping)

- **Priority**: medium
- **Batch**: unassigned
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/review.html.j2`, `src/media_hygiene/review/shots.py`, `src/media_hygiene/report/decisions.py`, `src/media_hygiene/services/burst_review.py`, `src/media_hygiene/services/review.py`, `src/media_hygiene/actions/clean.py`, `src/media_hygiene/actions/verify.py`, `src/media_hygiene/plan/similar_models.py`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_review_server.py`, `documentation/en/10-review-bursts.md`, `documentation/fr/10-review-bursts.md`

## Context

User feedback on 0.2.0 (2026-09-29): the review page has `A` (keep every shot) but nothing to
say "I want none of this series". Setting shots aside one by one stops at the last one ("Keep at
least one shot of the series."), and digits only reach the first 9 shots of a longer series.

"At least one shot kept" is enforced at every layer, not only on the page:

- page: no key; `set_aside_problem` (`review/shots.py`) refuses `len(discarded) == len(shots)`;
- file: `BurstDecision.kept` has `min_length=1` (`report/decisions.py`);
- `clean`: `BurstChoice` promises "only while at least one `kept` shot is still there";
  `burst_blocker` skips every shot when no kept shot is left (`any(())` is false), and
  `_quarantine_burst` reads `choice.kept[0]` as the journal's reference (IndexError on `()`).

Setting a whole series aside stays safe: the shots go to the quarantine, never deleted, and
`undo` brings them back; nothing happens before `clean --decisions`, and `A` restores the
series on the page.

## Proposal

- New key `X` ("set the whole series aside"): same character on AZERTY and QWERTY, next to the
  `S` / `A` legend. It sets aside every shot **not** in a protected folder; when every shot is
  protected, the usual "is in a protected folder" message. Pressing `X` again, or `A`, keeps
  them all again.
- The page shows the state clearly: every shot dimmed, a banner "Whole series set aside — the
  shots go to the quarantine at 'clean --decisions'".
- `BurstDecision.kept`: `min_length=0`; `discarded` keeps `min_length=1` (a series left whole is
  still not listed). The file stays `version: 1`: older files remain valid.
- `clean`: a choice with no kept shot skips the "a kept shot is still there" check (only
  `change_blocker`), and the journal entry has no reference file (as `ActionKind.QUARANTINE`)
  — or a dedicated kind if `history` / `undo` need to tell it apart (decide while
  implementing, see 0024).
- `clean --decisions` summary: also count the series set aside whole.

## Acceptance

- [ ] `X` sets every movable shot of the series aside, saved at once in the decisions file;
      `A` (or `X` again) undoes it.
- [ ] A series with a protected shot: `X` sets the others aside, the protected one stays kept.
- [ ] `clean --decisions` moves every shot of a series set aside whole to the quarantine;
      `undo` brings them all back (integration test).
- [ ] A shot of such a series that is also the kept copy of an exact-duplicate group: `clean`
      then `undo` leaves every file where it was (test).
- [ ] A decisions file written by 0.2.0 still loads.
- [ ] New strings translated (`i18n_update`), docs EN + FR (key table of step 10, what `X`
      does), screenshot refreshed with `docs_screenshots` if the legend is captured.
