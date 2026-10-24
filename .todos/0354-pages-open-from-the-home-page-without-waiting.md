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
