# 0692 — Home page ready at once after a restart, whatever the tool folders hold

- **Priority**: High
- **Batch**: page-speed
- **Depends**: —
- **Files**: `src/media_hygiene/review/templates/home.js.j2`, `src/media_hygiene/cli/home_state.py`, `src/media_hygiene/cli/status_safety.py`, `src/media_hygiene/services/safety.py`, `src/media_hygiene/services/only_copies.py`, `src/media_hygiene/review/home_app.py`, `tests/measure/mh-measure.ps1`
- **Needs maintainer**: the before/after timing on the Windows PC (Docker Desktop, real tool folders)

Filed 2026-11-10 after the maintainer's report.

## Context

Reported by the maintainer (Windows, Docker Desktop, timed by stopwatch, not measured by a tool):
`mh` → the home page shows *Préparation de l'accueil…* then *Lecture des dossiers de l'outil
en cours…* for about **30 s**. After stopping `mh`, removing the container and starting `mh`
again, with the photos left untouched, the wait is the same.

Why, from reading the code (not measured):

- `GET /api/state` → `home_state()` reads every tool folder again on each call (`/config`,
  `/journal`, every `/quarantine/<x>`, `/reports`, the index in `/cache`). Every stat goes
  through Docker Desktop's file sharing (0277). Nothing of the result is kept between two runs.
- The page keeps its last state in `sessionStorage` (`home.js.j2`, `keptState`). It is lost
  when the tab closes, so every new start waits for the full answer.
- Main suspect, *estimated*: the *Are my photos safe?* card (0689, commit 793c057b, landed after
  the speed review 9709f726). `only_copies()` reads the journal of each run still in quarantine
  and stats **every quarantined file**, on each home page call. `read_status` and `held_back`
  read the same quarantines again.
- The speed review of 2026-11-10 (0677, 0678) measured the devcontainer demo tree (28 files,
  no Docker Desktop sharing, empty quarantine): it could not see this cost.

## Proposal

1. **Measure first**: one step in `mh-measure.ps1` that times inside the container each part
   of `home_state` (`read_status`, `home_safety` split into `only_copies` / `held_back` /
   `reread_counts`, `home_folders`, `home_update`, `latest_reports`) on the real folders, a
   first call then a second one. Also time in the devcontainer on a synthetic quarantine of
   5,000 files (generator of 0678 if it exists).
2. **The page shows at once**: keep the last state in `localStorage` (try/catch, as now),
   drawn marked *updating…* (0442 already does this inside one tab). A first start ever still
   shows the meerkat.
3. **The slow parts leave the first answer**: `/api/state` without the safety card (and any
   other part above ~200 ms in step 1). The card comes from its own route, drawn when it arrives
   (its place keeps its size: no jump).
4. **The safety facts are cached**: in `/cache`, keyed by the journal files' and quarantine
   folders' (size, mtime) list; recomputed only when one changes. Invalidation events, one test
   each: a run added (clean), undo, purge, a file removed from the quarantine by hand, a drive
   quarantine mounted / unmounted, the journal restored by `mh backup`.
5. Say in the report whether the ~200 ms threshold should be a setting (expected: no, a constant).

## Acceptance

- [ ] Step 1's figures before / after, on the maintainer's PC (measured, each part)
- [ ] Second start of `mh` (container removed, nothing changed): the home page is drawn
      under 1 s, then updated
- [ ] The safety card shows the same facts as before (equivalence test), and follows each
      invalidation event above
- [ ] No traceback, no endless spinner if the card's route fails (message in the card)
- [ ] New strings through `_()` + French; both documentation languages if a capture changes
      (`docs_screenshots` to run afterwards)
