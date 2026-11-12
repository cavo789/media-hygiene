# 0572 — Search › Events: trust what the disk holds, not a classify plan the user forgot

- **Priority**: high
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/search/events_desk.py, src/media_hygiene/review/sort_progress.py, src/media_hygiene/search/templates/search_events*.j2, src/media_hygiene/review/templates/pick_grid.js.j2, documentation/en|fr/sort/

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
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
- [ ] Moved rows found by content; sorted-by-any-means counted (tests per move kind)
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
- [ ] Plan age shown, or the tab works without a plan (per the maintainer's choice)
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
- [ ] Docs en/fr (`sort/11-name-events-in-the-browser.md`); `docs_screenshots` flagged stale
  → captures: one run of `docs_screenshots`, tracked in 0717 (2026-11-12)

## Maintainer's answers (2026-11-02)

- **GO for events built on the fly** from the index for the period shown — no `classify`,
  no AI, no rules — provided it does not kill performance (measure on a 50,000-file
  index; say measured/estimated). Showing what is already sorted is useless and
  counter-productive.
- **"Not sorted yet" = the definition `/search` already uses** (`Sorting.LEFT` in
  `search/query.py`: not in a `YYYY/YYYY-MM/<name>` folder yet), whoever moved it. One
  definition everywhere in mh: reuse that code, never a second copy.

## Status — PARTIAL (2026-11-02)

### Done
- The Events tab builds its events on the fly (`search/span_events.py`): the files not
  sorted yet, by `/search`'s own condition (`Sorting.LEFT`, `search/statements.py`), cut at
  each gap longer than classify's `event_gap_hours`, for the page's From/To. No plan.json,
  no AI, no rules. A click fills the grid; 📂 Event… moves the picked photos.
- The grid is emptied before each load; on a failure it stays empty with the reason.
- Measured (synthetic 50,000-row index, 25,000 not sorted, `nice -n 19`, 3 runs): every
  date 0.28 s (8,284 events), one year 0.05 s, one event's tiles 0.05 s; whole process
  0.63 s, 81 MB peak (`/usr/bin/time`).
- Tests: `tests/integration/test_span_events.py`; docs en/fr `commands/search.md`, `sort/11`.

### Not done
- Remove the plan-based UI now hidden (`events_choice`/`events_sure`/`events_rule`/
  → code work, not the maintainer's: listed in 0718 (2026-11-12)
  `events_progress` templates, `EventsDesk.opener/state/event`, the sort routes of
  `events_choose`, their tests), and rewrite the rest of `sort/11` that still describes it.
  **Reason:** scope; a follow-up TODO.
- No browser test of the new JS; `docs_screenshots` stale for `/search` (Events tab).
  → browser check: CI's job (headless Chromium), not the maintainer's (2026-11-12)
- Decided 2026-11-02: the gap stays classify's setting (one definition of an event).
  → nothing left to do: a decision already taken, kept as is (2026-11-12)

## Closed by the inbox (2026-11-12)

Nothing left for the maintainer: each item above is answered (`→`); the code work left is
listed in 0718, the captures in 0717.
