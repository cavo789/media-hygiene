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
