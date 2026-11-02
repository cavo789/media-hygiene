# 0572 — Search › Events: trust what the disk holds, not a classify plan the user forgot

- **Priority**: high
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/search/events_desk.py, src/media_hygiene/review/sort_progress.py, src/media_hygiene/search/templates/search_events*.j2, src/media_hygiene/review/templates/pick_grid.js.j2, documentation/en|fr/sort/
- **Needs maintainer**: the choice in "Questions" below

## Context (maintainer, 2026-11-02)

The maintainer sorts from `/search` only: picks a period, selects photos, clicks
**Event**, and moves them. They never run `mh classify` ("I forget it exists"). Yet the
**Events** tab of `/search` is entirely built on the latest `plan.json` of `classify`
(here `20261013-191349-classify`, 1,137 events, 52,056 rows, three weeks old):

- **"Only the events not sorted yet"** keeps events the maintainer has sorted:
  `sort_progress` counts as *sorted* only the rows a `sort` run **of that plan** moved.
  Read-only on their journal (measured 2026-11-02): ~350 runs since 2026-10-25 (move
  dialog, imports, decisions) carry no plan id, 66 belong to the plan. `mh audit` does not
  refresh the plan, so re-auditing changed nothing.
- **The grid kept the Photos tab's results** ("40,730 files found; the first 240 shown",
  photos of 2026-10-30) while the card said "Event 58 of 1137" — a 2005 event of 35 rows
  ("Extérieur Maison"). Likely: `/api/events/<id>` failed (`refresh` returns on
  `!answer.ok` without clearing the grid), or the event's rows were looked up only at
  their plan path (`_tiles`) after they moved. Not reproduced yet.
- `mh classify` rerun prints one warning per multi-level rule (fixed 2026-11-02: one line)
  and asks the AI model for unmatched groups — heavy for a user who only wanted to see.

## Wanted

1. **Never show another tab's grid under an event**: on any failure, empty grid + the
   reason in the status line. Reproduce first (moved event rows, unknown id).
2. **Follow moved files** in the Events tab and in its counts: a plan row whose path is
   gone is found by `sha256` (+ size) in the index (as 0570 does for place photos); a row
   now in a dated `YYYY/YYYY-MM/<name>` folder (sorted by any page, any run, Explorer)
   counts as sorted. Tests: moved by the move dialog, by `sort`, renamed in Explorer.
3. **Say the plan's age**: "This list comes from classify of 13 Oct; N of its files have
   moved since" with the way to refresh it — or (see Questions) drop the dependency.

## Questions for the maintainer

- The Events tab without any `classify`: build the events on the fly from the index for
  the period shown (date gaps, as `classify` does, no AI, no rules) — or keep the plan
  and offer to refresh it from the page?
- Should the "not sorted yet" filter mean "not yet in a `YYYY/YYYY-MM/<name>` folder",
  whatever moved it?

## Acceptance

- [ ] Grid never stale under an event (test)
- [ ] Moved rows found by content; sorted-by-any-means counted (tests per move kind)
- [ ] Plan age shown, or the tab works without a plan (per the maintainer's choice)
- [ ] Docs en/fr (`sort/11-name-events-in-the-browser.md`); `docs_screenshots` flagged stale
