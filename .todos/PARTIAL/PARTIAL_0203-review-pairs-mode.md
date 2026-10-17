# 0203 — `review --pairs`: decide the folder pairs in the browser, saved where `clean` reads them

- **Priority**: Medium
- **Batch**: review
- **Depends**: —
- **Files**: `src/media_hygiene/cli/cmd_review.py`, `src/media_hygiene/cli/review_modes.py` (new), `src/media_hygiene/cli/review_options.py`, `src/media_hygiene/services/pairs_reviewing.py` (new), `src/media_hygiene/review/pairs_app.py` (new), `src/media_hygiene/review/pairs_views.py` (new), `src/media_hygiene/review/pairs_file.py` (new), `src/media_hygiene/review/templates/pairs_review.html.j2` (new), `src/media_hygiene/review/templates/pairs_review.js.j2` (new), `src/media_hygiene/report/decisions.py`, `src/media_hygiene/report/templates/_decisions.html.j2`, `src/media_hygiene/i18n/locales/fr/LC_MESSAGES/media_hygiene.po`, `tests/integration/test_pairs_review.py` (new), `tests/support/docs/pages.py`, `documentation/en/clean/12-decide-pair-by-pair.md`, `documentation/fr/clean/12-decide-pair-by-pair.md`, `documentation/en/commands/review.md`, `documentation/fr/commands/review.md`

## Context

Chosen by the maintainer on 2026-10-17 (proposal A6: the report's decisions without a download).
Step 12 of the cleaning guide: the report's *Folder pairs* table offers *As planned / Swap the
folders / Leave alone* for each pair, but a page opened from the disk cannot write a file. The user
clicks *Download decisions.json*, moves the file from Downloads into the reports folder, then runs
`mh clean --decisions`. Users stop at such steps.

`review` (bursts) and `review --near` already save each choice at once into `decisions.json`
(read back from the disk and shown), under their own key, keeping the other keys. A third mode
does the same for the folder pairs. It needs no home page (the home page, F5, links to it).

## What to do

- `review --pairs`: audit, then serve the folder pairs one at a time, the largest first, each with
  its sample previews and evidence (`PairEvidence`: the reasons, the samples, "entirely a copy"),
  and the keys of the other reviews: `→` as planned, `W` swap (refused when the kept side is
  protected, as in the report), `L` leave alone, `U` back to undecided, `←` and `N`.
- Each choice is saved at once under `pairs` (the `PairDecision` model the report writes), the
  other keys kept, then read back and shown, as `review --near` does (`review/near_file.py`).
- Size caps: `cmd_review.py` (170/200) dispatches its modes from a new `cli/review_modes.py`;
  `report/decisions.py` is full (200/200): what the pairs file needs goes to `review/pairs_file.py`.
- The report: next to *Download decisions.json*, one line: "Or decide in your browser, saved for
  `clean`: `mh review --pairs`".
- `mh`: nothing new (`review` is already a page command).
- A capture of the new page for the docs (`tests/support/docs/pages.py`, synthetic pictures only).

## Explicit non-goals

- The report keeps its lists and its download: a report opened alone, offline, still works.
- No new kind of decision: the "link" choice is 0213, which adds its key to this page.

## Acceptance

- Integration (HTTP, as `tests/integration/test_near_review.py`): the state lists the pairs; a
  choice is saved and read back; a swap of a protected pair is refused; the `bursts` and `near`
  keys of an existing `decisions.json` are kept; `clean --decisions` then applies the pairs.
- Docs both languages: step 12 shows `mh review --pairs` first and the download as the offline
  way; the `review` command page. Say in the report that `docs_screenshots` should run.

## Gain (estimated)

Deciding folder pairs: three steps outside the tool (download, find the file, move it) → none;
and each choice proven saved (read back from the disk) instead of trusting a download.

## Status — PARTIAL (2026-10-17)

### Done
- `review --pairs` (`cli/review_modes.py`, `cli/pairs_review_flow.py`, `services/pairs_reviewing.py`,
  `review/pairs_app.py`, `pairs_session.py`, `pairs_views.py`, `pairs_file.py`, templates
  `pairs_review.html.j2` / `.js.j2`): pairs the most space freed first, samples, reasons,
  "entirely a copy", keys `→` `W` `L` `U` `←` `N`; each choice saved under `pairs`, read back and
  shown; the other keys of `decisions.json` kept; swap refused on a protected kept folder or a
  pair inside one folder (the same rule as `clean --decisions`).
- New `PairAction.PLANNED` (`planned`): a pair seen and left as planned stays decided when the
  review resumes; `clean --decisions` ignores it (never refused as stale either).
- `cmd_review.py` dispatches `--near` / `--pairs` from `cli/review_modes.py` (one mode per run).
- The report: "Or decide in your browser, saved for 'clean': mh review --pairs" under the download.
- Shared code: `services/review_serving.py` (one page server for near, pairs, junk),
  `review/decide_route.py` (`DecidingApp`), `review/keyed_choices.py`, `cli/review_next.py`.
- Docs both languages: step 12 shows `mh review --pairs` first, the report's download as the
  offline way; the `review` command page. French `.po` complete.
- Integration tests `tests/integration/test_pairs_review.py` (state, choice read back, protected
  swap refused, other keys kept, resume, `clean --decisions` applies, CLI lines, page render).
- Docs capture wiring: `review-pairs.txt` (terminal) via `browsing.py` / `served.pairs`.

### Not done
- The screenshot of the page in the docs (`review-pairs.webp`).
  **Reason:** images come only from `docs_screenshots` (not run in an unattended lot); a page
  linking an image that does not exist yet fails `test_documentation.py`. Next step: in
  `tests/support/docs/served.py::pairs`, add `page.screenshot(path=SHOTS / "review-pairs.png")`
  after the wait, run `docs_screenshots`, then show `../images/review-pairs.webp` in step 12
  (both languages).
