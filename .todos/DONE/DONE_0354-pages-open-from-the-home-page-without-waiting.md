# 0354 — Pages opened from the home page in under a second: measure each phase, then cut

- **Priority**: High
- **Batch**: home
- **Depends**: —
- **Files**: `tests/measure/mh-measure.ps1`, `src/media_hygiene/cli/templates/mh_menu.ps1.j2`, `src/media_hygiene/cli/templates/mh.ps1.j2`, `src/media_hygiene/review/home_app.py`, `src/media_hygiene/review/home_step.py`, `src/media_hygiene/review/home_fields.py`, `src/media_hygiene/services/search_pages.py`, `src/media_hygiene/person/door.py`
- **Needs maintainer**: step 35 of `mh-measure.ps1` on Windows + Docker Desktop, with their own mh and cache (about 10 minutes, *estimated*: 3 rounds of 2 clicks, plus one page of their choice)

## Context

Reported by the maintainer (2026-10-24): every click on the home page waits several seconds, even
`search`, which "should only show its page". Read in the code, a click on a page runs:

1. The home page's server ends with exit code `STEP_EXIT_BASE + n` (`review/home_app.py`), its
   container stops.
2. `mh.ps1` runs **a whole container** `mh menu` only to read which command step `n` is
   (`mh_menu.ps1.j2`, `$steps = @(mh @color menu)`).
3. `mh.ps1` runs the step's container: guards first (`docker ps`, the port, removable drives:
   `docker` CLI calls), then `docker run`; inside, Python, the CLI, the step's code, the index
   opened, and for `search` the names of the people read from the faces, the vectors counted; the
   full-text table built from every tag at the first search (in the connection's `temp`
   schema, never kept: 203,246 words over 44,488 files on the maintainer's index, their console).
4. Back to the home page: one more container, the state of the tool folders read again.

Known figures:

- An empty `docker run` on the maintainer's PC: 0.6 s (*measured*, 0277, step 23f).
- The code of `search_pages` loaded: 0.3 s, of which 0.26 s for `person.door` → `faces.worker`
  → numpy (*measured*, devcontainer, `python -X importtime`, 2026-10-24).
- The phases of `search` before its page answers, on the demo tree: 375 ms in all (*measured*,
  devcontainer, the code of step 35c, 2026-10-24); on a real index: unknown.
- Total felt by the maintainer: "several seconds" per click (not timed).

## Measured (step 35, maintainer's PC, image `media-hygiene` local build, 2026-10-24)

Click "search" on the home page → search page shown: **7.6 s and 8.7 s** (rounds 1 and 2, from
the home container's `die` to the maintainer's Enter; round 3 got no Docker events). Round 2:

| Phase | Time | Share |
|---|---|---|
| home container stops after the click | 0.2 s | 2 % |
| `mh menu` container, only to read the step chosen (35b alone: 2.1–2.3 s) | 2.5 s | 28 % |
| guards of `mh.ps1` before `docker run` (between the two containers) | 0.5 s | 6 % |
| search container start → page shown | 5.4 s | 62 % |

Inside the search container (35c, twice, same figures): **2.8 s**, of which
**names of the people read 1.8 s** (`people_words`, 11,457 photos named), locale 0.28 s, CLI 0.09 s,
code 0.17 s, settings 0.08 s, index opened 0 s (226 MB), first search 0.37 s (the full-text
table built), next ones 2 ms. A bare container: python 0.3 s, `--version` 0.58 s (35a). The rest
of the 5.4 s (≈ 2.6 s) is the tab's wait for the new server (polled every 1 s,
`home_link.html.j2`), the page's first requests and the maintainer's reaction (*estimated*).

"Back to the home page" → home page shown: 4.8 s and 5.6 s once it worked (rounds 2, 3); new home
container started 0.5–0.65 s after the search one died; start → shown 3.4–4.1 s. **Round 1: the
tab stayed on the search page, F5 needed (26 s)** — the bug below.

**Bug, read in the code**: `awaitHome` (`review/templates/home_link.html.j2`, and
`waitForComeBack` in `home_run.js.j2`) polls `/` every 1 s and reloads only after one poll
*failed* (`seenGone`). The gap between the old server's end and the new one's start is 0.5–0.65 s
(*measured* above), shorter than the poll: when no poll falls into it, the tab never sees the
server gone and waits forever. Fix: each server answers its own start id (a header or a field of
`/`); the tab reloads when the id differs from the one it was served, polling every 250 ms.

## Done (2026-10-24, not yet measured on Windows)

- No `mh menu` container after a click: `home_step._handed` writes the step's words into
  `.mh-step.json` and ends with the fields code, which every `mh.ps1` / `mh.sh` since 0266
  already runs (no `mh update` needed); reports in a named volume, or the file not writable:
  the number, as before. `mh.sh` rings its bell for a console step only, as from `mh menu`.
  *Apply now* (browse, reviews) still ends on its number: rare, and its pages do not know the
  reports folder.
- The tab waiting for the next server: `X-Media-Hygiene-Run` on every answer
  (`review/respond.py`), compared with the run that took the click, polled every 250 ms
  (`home_run.js.j2`, `home_link.html.j2`, `apply_now.html.j2`, `phone_review.js.j2`).
- `search` / `browse` / `slideshow`: the names of the people read in a thread
  (`search/names_soon.py`), taken at the first search (`MeaningIndex._fresh`); the start's
  "no file has words" check reads one tag row instead of a search. Gain *estimated* at
  0.3–1 s only: the page searches as soon as it loads, so it waits for the rest.
- To do: run step 35 again on the maintainer's PC (image rebuilt), before → after here.

## What to do

1. **Measure first** — step 35 of `tests/measure/mh-measure.ps1` (written with this TODO, nothing
   written on the PC):
   - 35a: a container running `python -c pass`, and `media-hygiene --version`: the container's own
     price;
   - 35b: `mh menu` with their own mh, three times: the price of step 2 above;
   - 35c: inside a container with their cache and config read-only, each phase of `search`
     before its page answers (locale, CLI built, code loaded, settings, index opened, people,
     meaning, three searches: the first builds the full-text table);
   - 35d: by hand, 3 rounds of "home → search" and "search → home" (plus one page of their choice):
     the time between two Enters and Docker's own events between them (which containers die and
     start, when), two marker volumes giving both Enters in Docker's clock;
   - 35f: which wait bothers them most.
   Command: `.\mh-measure.ps1 -Only 35 -Count 1`.
2. **Then cut, ranked by the measures** (each one *estimated* until step 35 says):
   - **No `mh menu` container after a click** (≈ 1 s, *estimated*: one `docker run` + Python):
     the home page writes the words of the step chosen into the one-shot file it already writes
     for the steps with fields (0266, `home_fields.py`), and `mh_menu.ps1.j2` reads them for every
     step, never `mh menu` again in the loop. Keep the refusal of a step the launcher did not allow.
   - **Lazy imports in the pages** (≈ 0.3 s, *measured* in the devcontainer): `person.door` and
     the faces worker loaded when a face is asked, not when `search` starts.
   - **The full-text table**: if 35c shows its first build above a few hundred ms on the real
     index, keep it in a file of `/cache` (rebuilt when `data_version` or the tags changed) or
     build it while the page loads its first screen.
   - **One server for the home page and every page** (the click becomes instantaneous: no
     container between the two pages): only if the measures show the container itself is most
     of the wait. It changes how every page is served and how `mh` runs the steps (the home page
     already serves `/docs/`): list what it loses (one container per step: its own mounts, `:ro`
     for read-only commands, a crash ending one page only) and ask the maintainer before
     starting. Its own TODO if chosen.
3. Each cut: before → after on the maintainer's PC (step 35 again), in the commit message.

## Acceptance

- Step 35's results read back, the phases ranked in a table here (measured).
- "home → search" and "search → home" each under 1 s on the maintainer's PC, or the measured
  reason why not and the decision taken with the maintainer.
- The steps with fields and the refused steps work as before (tests of `mh_menu`).

## Gain

Today: several seconds per click (felt, not timed), of which ≈ 1 s for `mh menu` and ≈ 0.6 s per
container (*estimated* from 0277's 0.6 s). After the two quick cuts: about 1.3 s less per click
(*estimated*); with one server: under 0.2 s (*estimated*: the page's own requests only). The
maintainer clicks dozens of times per session.

## Status — PARTIAL (2026-10-24)

### Done
- The three cuts listed under *Done* above (commit `aabd24c`); the single server chosen by the
  maintainer and split into 0355–0361.

### Not done
- Step 35 run again on the maintainer's PC (image rebuilt) to write before → after here.
  **Reason:** a measurement only Windows + Docker Desktop gives.

## Validated on Windows (2026-10-25, maintainer, by hand)

The image of `iterate/2026-10-24` and its `mh.ps1` (`mh update`): `mh` alone opens the home page;
search shows at once and the way back needs no F5 (step 35's timing by two Enters dropped as
meaningless now: real timings in the browser test of 0366); a console step chosen on the page
(*See what each run did*, `mh history`) runs in the PowerShell window while the home page stays
open; Quit, then `mh` again, works. The crash restart left by 0355 is TODO 0365.
