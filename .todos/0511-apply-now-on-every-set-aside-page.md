# 0511 — *Apply now* on every page that sets files aside, enforced by a test

- **Priority**: High
- **Batch**: reviews
- **Depends**: 0510 (the intruders page gets its Apply there)
- **Files**: `src/media_hygiene/services/gone_reviewing.py`, `src/media_hygiene/services/review_serving.py`, `src/media_hygiene/review/templates/gone_review.html.j2`, `.claude/skills/photo-picking-pages/SKILL.md`, `tests/unit/` (new test), `documentation/en/clean/`, `documentation/fr/clean/`

## Reported (maintainer, 2026-10-30)

"Every page that lets you set aside should offer the Apply button; it should be part of our
standards." Rule added the same day to `.claude/rules/workflow.md` (product rules).

## Today (read, 2026-10-30)

`ApplyOffer` is built by the bursts (`review_kinds.py`), pairs, near, unwanted reviews,
`search`, `people`. Missing:

| Page | Records | Apply |
|---|---|---|
| `review --intruders` (`intruders_reviewing.py`) | files set aside | none — fixed by 0510 |
| `review --gone` (`gone_reviewing.py`) | "deleted on purpose", applied by `clean --decisions` | none |

To check: `shrink` (its page, if it picks files for `shrink --apply`), and any page added
since. The phone pages stay read-only (no Apply: nothing is set aside off the PC).

## To do

1. `review --gone`: an `ApplyOffer` (pending = some answer saved), the shared `apply_now`
   template at the same place in the bar.
2. Check `shrink` and every `*_app.py` writing a decisions file; add Apply where something
   waits for a run, or say in this TODO why not.
3. A test listing every review kind / page that writes `decisions.json` (from the kinds'
   registry, not a hand list) and asserting each offers an `ApplyOffer`: a new page without
   it fails.
4. Skill `photo-picking-pages`: say the rule also binds pages without tiles (intruders,
   gone).
5. Docs EN + FR of the gone page; `docs_screenshots` should then run — not run by the TODO.

## Where the user gains

Before: on two pages, set aside, then go find and type `clean --decisions`. After: the same
*Apply now* on every page, and a test so a new page cannot forget it.
