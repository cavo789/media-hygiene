# 0315 — Freeing a phone: "Apply now", then the page again with what is left

- **Priority**: Medium
- **Batch**: phone
- **Depends**: 0312
- **Files**: `src/media_hygiene/cli/templates/mh_phone_free.ps1.j2`, `src/media_hygiene/services/launcher_phone_free.py`, `src/media_hygiene/cli/cmd_phone_review.py`, `src/media_hygiene/review/phone_app.py`, `src/media_hygiene/review/phone_session.py`, `src/media_hygiene/review/templates/phone_review.html.j2`, `src/media_hygiene/review/templates/phone_review.js.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `documentation/en/commands/launcher.md`, `documentation/fr/commands/launcher.md`, `tests/integration/test_phone_review.py`, `tests/unit/test_launcher_phone.py`

## Why

The maintainer, 2026-10-23: "I would like to *Apply now* as on the `browse` page: I really
delete some photos and stay in the `mh phone` page to clean step by step" — one folder, then
the next, seeing the phone empty as they go.

## Why it is not browse's button

`browse`'s **Apply now** (`apply_now.html.j2`) ends the server with the code of a home step
that `mh` then runs in the terminal, and the home page comes back on the same port. On the
phone, the container cannot reach the phone at all: `mh.ps1` deletes, over USB with
`Shell.Application` (`_phone_clear` in `mh_phone_free.ps1.j2`: copy again → proof in the
container → `MoveHere` → list again → journal). The page ending is what hands the ticked
files to PowerShell (`phone-review` prints them on stdout). So "stay in the page" means a loop
in `mh.ps1`, not a new route.

## What

1. `_phone_clear` loops: page → the ticked files deleted (as today, batch by batch, proved) →
   the phone listed again → the plan rebuilt for the files left → **the page again, on the same
   port**, which the open tab finds back by itself (as the home page does after a step: it
   saw the server gone, then answering, 0280) — no second tab.
2. The page tells what the last round did, read from the journal (not from memory): "N files
   deleted from the phone (X GB); M kept: they differed from the PC's copy" — the same counts
   the console prints today.
3. Two buttons: **Delete the ticked ones now** (comes back) and **Done** (ends, the console's
   usual summary for the whole session). Ticks of files still on the phone are kept across
   rounds (`phone-decisions.json`, keyed by the phone's path — what happens if the user
   renames a folder on the phone between two rounds: the file is offered again, unticked).
4. While PowerShell deletes, the tab shows a waiting state ("Switch to the PowerShell window:
   the files leave the phone one by one…") with the estimate the console already computes.

## Tests

- Integration: two rounds of the page with a fake list of phone files; the second round holds
  only the files not deleted, their earlier ticks kept.
- `test_launcher_phone.py`: the rendered `mh.ps1` loops back to the page and stops on Done.

## Measure

The round trip (page closed → files moved → page back) on the maintainer's phone: a step in
`tests/measure/mh-measure.ps1` if it is slower than a few seconds for 20 files (estimated from
the per-file speed in `launcher_phone_free.py`, to check).

## Docs

The launcher page's section on freeing the phone (both languages); `docs_screenshots` should
run afterwards (not unasked).

## Status — PARTIAL (2026-10-23)

### Done
- Point 4, the waiting state: after *Delete*, the tab says "Switch to the PowerShell window:
  the files leave the phone one by one, each one copied again and compared with the PC's copy
  first (about N min)", N from the console's own formula (2 reads, `PHONE_MB_PER_SECOND`,
  rendered as `phone_speed`). Checked in headless Chromium (mocked API).
- The groundwork 0332 laid: opened from the home page, the phone page's tab follows its
  server back (`window.mhAwaitHome` of `home_link.html.j2`: seen gone, then answering → the
  page shown again); the same mechanism a second round of this page needs on the same port.

### Not done
- Points 1–3: the loop of `_mh_phone_clear` (page → batches proved and moved → phone listed
  again → `phone-plan` again → the page again on the same port), the round's summary read
  from the journal, the two buttons (*Delete the ticked ones now* / *Done*), the ticks kept
  across rounds in `phone-decisions.json` keyed by the phone's path.
  **Reason:** the loop re-lists the phone over MTP between rounds (`_mh_phone_files`, now in
  `_mh_phone` only, must move into a function both call) and changes how the page's end is read
  (a code for "round" vs "done"): only PowerShell 5.1 with a real USB phone proves it; the
  devcontainer can render the script as text only. Writing it unrun next to the
  proof-before-delete steps was judged unsafe in an unattended lot. Needs a session with the
  maintainer's phone, or one dedicated to it with a step in `tests/measure/mh-measure.ps1`
  (two rounds of 20 files, the round trip timed).
- The two-round integration test and the `test_launcher_phone.py` loop test: they follow the
  loop.
- The measure (round trip for 20 files): follows the loop; estimated from 24 MB/s × 2 reads
  plus ≈ 2 s per container start and the re-listing (not measured).
