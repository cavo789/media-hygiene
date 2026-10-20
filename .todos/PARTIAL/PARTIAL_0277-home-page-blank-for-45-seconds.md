# 0277 — Home page blank for about 45 seconds before it shows

- **Priority**: high
- **Batch**: unassigned
- **Depends**: —
- **Files**: src/media_hygiene/review/home_app.py, src/media_hygiene/cli/home_state.py, src/media_hygiene/review/templates/ (home page), tests/unit/ (home), tests/measure/mh-measure.ps1
- **Needs maintainer**: a timing run on the Windows PC (Docker Desktop, real `C:\Photos`)

## Context

The maintainer double-clicked the desktop shortcut (2026-10-20). The console printed at once:

```text
✅ Accueil prêt, ouvrez http://127.0.0.1:8088/ dans votre navigateur. Ctrl+C l'arrête.
Votre navigateur s'ouvre sur http://127.0.0.1:8088/ ; sinon, ouvrez cette adresse.
```

The browser then stayed on a **blank page for about 45 seconds** (estimated by the maintainer,
not measured) before the home page appeared. A first impression this slow reads as "broken".

## Suspect (from reading the code, not measured)

`GET /` (`HomeApp._read`, `home_app.py`) builds the whole state **before sending a single byte**:
`await asyncio.to_thread(self.state)` → `home_state()` (`cli/home_state.py`), which calls in
sequence:

- `read_status(runtime)` — journal, quarantines (every drive), index (SQLite in `/cache`),
  decision files; on a Docker Desktop bind mount of `C:\` every stat is slow;
- `home_update()` → `newer_version()` — a Docker Hub request (`TIMEOUT_S`) when the cached
  answer is stale; offline or slow DNS can cost the whole timeout;
- `home_folders(runtime)` — may walk or stat the photo folders under `/data`;
- `latest_reports()`, `audit_previews()` — list `/reports`;
- `windows_menu()`, `full_catalog()`.

Any one of them, on the real collection through Docker Desktop's file sharing, can explain it.

## Plan

1. **Measure first** (skill `measure-before-ranking`): time each call of `home_state()`
   separately — locally on the demo tree, and on the maintainer's PC via a new step in
   `tests/measure/mh-measure.ps1` (cold start of the container, then a second load). Label
   each figure measured/estimated.
2. Fix the slow parts found (cache, skip, or move off the first answer — e.g. the update check
   in the background, folders counted later).
3. **In any case, never a blank page**: `GET /` answers at once with the page shell and a
   loading screen showing the meerkat (`home_assets`, images of the redesign 0265–0269) and a
   short "Préparation de l'accueil…" line; the page then fetches `/api/state` (already served:
   `STATE_PATH`) and draws. Slow parts may fill in afterwards (progressive tiles).
4. Tests: `GET /` answers without calling `state`; the loading screen is replaced once the
   state arrives; an error while reading the state shows a message, not an endless spinner.
   New strings through `_()` + French; both docs languages if a capture changes
   (`docs_screenshots` to run afterwards — not run here).

## Done when

- The first paint after the shortcut is under 1 s (measured on the maintainer's PC).
- The full home page time is measured before → after and reported in %.
- Whether a threshold (e.g. update-check timeout) should be a `config.toml` setting is stated.

## Same slowness on every click (2026-10-20)

Once the page showed, the action buttons (**Lancer**, **Ouvrir la page**) looked dead: the
reaction came, but very late, with no sign of activity in between (first filed as 0280,
withdrawn by the maintainer: it works, only slowly). The "Media Hygiene est arrêté" overlay
then appeared, the console still open — likely the step's `POST /api/step` ending the server
as designed, shown long after the click. So the cause is probably shared with the blank start:
find what makes the server slow to answer, and give each click immediate feedback (busy state
on the button, "the step starts in the console…") so it never reads as "nothing happens".

## Status — PARTIAL (2026-10-20)

### Done
- Measured in the devcontainer (demo tree, 32 files, `hygiene home` from sources): `GET /` 0.33 s
  cold, `GET /api/state` 4 ms, `POST /api/step` 4 ms; `home_state()` 2.6–3.7 ms, 7 `stat` +
  4 opens in `read_status`. Idle or half-sent connections do not block the server. So nothing
  in the code alone explains 45 s: the cause is on the Windows side (Docker Desktop file
  sharing of the real tool folders, DNS, `docker run` start).
- `GET /` no longer waits for `home_state()`: the page is served at once with a waiting meerkat
  (`#loading`, "Préparation de l'accueil…", a second line after 5 s), then fetches
  `/api/state`; a failure shows the stopped dialog, never an endless spinner. Presence (0261)
  starts before the state arrives, so a slow state cannot stop the server for "no tab".
- A click on Run / a form sent shows at once a toast "Envoyé : l'étape démarre dans …" and a
  busy button, before the server answers.
- `mh-measure.ps1` step 23 (`-Only 23 -Count 1`): with the user's own `mh` home page open, times
  `GET /` and `/api/state` from Windows, each part of `home_state()` inside the container
  (`docker exec`), the DNS of hub.docker.com, the file counts of the tool folders, and an empty
  `docker run` (the price of each step's round trip: one run for the step, one for the page).
- Test: `GET /` answers without reading the state; `/api/state` reads it.

### Not done
- The Windows measurement (step 23) and the fix of whatever it shows slow; the "first paint
  under 1 s" and before → after in % on the maintainer's PC.
  **Reason:** only the maintainer's PC (Docker Desktop, real folders) shows the slowness.
- Suspects to check against step 23: `urlopen(timeout=3)` does not bound the DNS lookup of
  the update check (answer cached a day, so at most once a day); `read_status` on large
  journals/quarantines; the two `docker run` per step chosen (likely the slow clicks).
- Setting: none added; `LOADING_SLOW_MS` (5 s) is cosmetic, not worth a `config.toml` key.
- `docs_screenshots` should run (the home page's first frame changed), not run here.
