# 0718 — The code work the PARTIAL TODOs left (gathered by the inbox of 2026-11-12)

- **Priority**: Medium
- **Batch**: backlog
- **Depends**: —
- **Files**: see each section (the source TODO names its files)

Filed by `/todo:inbox` on 2026-11-12. The inbox listed every `### Not done` item and unticked
acceptance box of the PARTIAL TODOs as waiting for the maintainer; 166 of them were code
work (or a check Claude can make against the code), none the maintainer's. Each now carries
`→ code work, not the maintainer's: listed in 0718`; the PARTIAL TODOs left with nothing for
the maintainer were moved to `DONE/` (their remaining work is here).

## How to use it

Not one job: an index. When planning, take one section (one source TODO), read the source
file for its context, check each item against the code first (many acceptance boxes may be
done already and only unticked), then file a focused TODO for what is really left
(skill `todo-authoring`) and strike the section here. Close 0718 when every section is struck.

## Items, by source TODO

### 0269 — `.todos/PARTIAL/PARTIAL_0269-open-the-home-page-from-a-phone.md`

- Moving the questions of the acting commands (`clean`, `undo`, `purge`, `sort`, `import`)

### 0315 — `.todos/DONE/0315-phone-page-apply-now-and-come-back.md`

- Points 1–3: the loop of `_mh_phone_clear` (page → batches proved and moved → phone listed
- The two-round integration test and the `test_launcher_phone.py` loop test: they follow the
- The measure (round trip for 20 files): follows the loop; estimated from 24 MB/s × 2 reads

### ~~0339~~ — done 2026-11-12: `tests/support/places_frame_walk.py` (Chromium, CI e2e)

### 0349 — `.todos/DONE/0349-albums-page-links-to-a-chapter-explaining-albums.md`

- The shared header's documentation links and the catalog `doc` of "Your albums" (it is a `Group(extra="albums")`, not a `Step`).
- `/albums` (empty or not, PC and paired phone) shows a documentation link that opens the new
- `tests/unit/test_documentation.py` and `test_docs_site.py` pass (links, parity, nav).

### 0359 — `.todos/PARTIAL/PARTIAL_0359-home-server-follows-usb-sticks-and-the-nas.md`

- The NAS checked every minute (asynchronous port 445), item 2's NAS half, and item 4 (a NAS
- Item 3: *Remove the USB stick* button and `mh eject E:`. **Reason:** scope.
- Item 5: files of a missing folder opened from search/browse say *not plugged in*. **Reason:** scope.
- *Also*: `mh search` in another window opening the tab on the running home server. **Reason:** scope.
- That the open tab reloads by itself after the restart (0354's `X-Media-Hygiene-Run`) is not

### 0361 — `.todos/PARTIAL/PARTIAL_0361-pages-that-write-run-their-writes-as-steps.md`

- Items 1, 4: shrink's page (`--try`, its own container) moved to the home server under a prefix
- Item 5 (a write from the server fails on its read-only mounts): needs the server's mounts in

### 0373 — `.todos/DONE/0373-video-thumbnails-from-a-keyframe.md`

- The album page (`share/album_view.py`) and the slideshow's phone grid (`slideshow/pictures.py`)
- An HEVC `.MOV` in the large view: Edge plays it only with the HEVC extension installed; not

### 0423 — `.todos/DONE/0423-ci-tests-job-off-the-critical-path.md`

- Medians of the Tests vs e2e jobs over at least three green runs, and the decision to split
- Options left for the documentation library if the Tests job stays the critical path: a

### 0430 — `.todos/PARTIAL/PARTIAL_0430-phone-app-over-https.md`

- iOS `.mobileconfig` download (Safari installs the `.crt` as a profile already).
- `<pc>.local` (mDNS) as an alternative to the DHCP reservation.

### 0432 — `.todos/PARTIAL/PARTIAL_0432-phone-installable-app.md`

- iOS startup images per screen size (`apple-touch-startup-image` with `media` queries):

### 0463 — `.todos/DONE/0463-search-page-compact-fixed-layout.md`

- Item 6, active filters as chips above the grid (« 3 filters · ✕ clear all »).

### 0478 — `.todos/DONE/0478-import-clean-in-one-go.md`

- Decided 2: the burst page opened on the import's bursts only, with tags/places/name running in
- Decided 3: the slideshow of the new event only (`slideshow` has no `--since`/files option yet;
- Decided 4 and 5 (rest of 0475/0476): home-page chain followed live, resume after interruption,
- `copies` runs after `tags` (it lives in `phone-end`): the 🤖 model also describes the copies

### 0481 — `.todos/DONE/0481-home-page-import-chain.md`

- The chain followed live on the home page, a chain stopped halfway resumed from the next

### 0498 — `.todos/DONE/0498-reports-in-home-look.md`

- The reports opened inside the home page's own frame (server-rendered with `shell*.j2` and the current-space highlight): the report files are static and served as-is by `review/report_files.py`; the http reveal is a client-side stand-in.

### 0505 — `.todos/DONE/0505-home-run-container-steps-in-a-popup.md`

- `people --forget` and `restore` (they prompt: need a "yes" flag skipping the console
- `backup` names the zip it wrote (its own output); not re-read from disk by the page.

### 0510 — `.todos/DONE/0510-intruders-page-sticky-actions-and-live-sentence.md`

- Point 6 (page opened behind): filed as TODO 0577.
- Sentence tests in pytest for the four cases (EN + FR): the logic is JavaScript; checked in

### 0513 — `.todos/DONE/0513-one-interface-every-action-from-the-page.md`

- The 32 steps. **Reason:** an umbrella; the work is 0586 (writing steps, needs a Windows run), 0506
- The chapter saying "everything from here": it would be false before that.

### 0514 — `.todos/DONE/0514-long-steps-followed-in-the-page.md`

- Points 1, 2 (Stop), 3, 5: run the long steps in the home container itself, a Stop button,
- Point 3 also drops `mh`'s second question before acting (the page's confirm would replace

### 0521 — `.todos/DONE/0521-undo-toast-instead-of-confirm.md`

- Moving files to an event (`search_rule.js.j2` goAsk) and *Apply now*: the toast's Undo
- Places (a place given photos, a place deleted) and albums (deleted, a photo taken out):

### 0526 — `.todos/DONE/0526-sort-trial-on-a-sample.md`

- The page side: a *Try on one month* button on the sort/Events page of `library`, then the
- The suggested "sort the rest" command is plain `sort` (latest workbook): a named workbook

### 0534 — `.todos/DONE/0534-album-root-chosen-on-the-page.md`

- The decided move: album link folders recreated in the new folder, the old one emptied of its
- A tree folder chooser (the field is a typed path). **Reason:** the search tree lists the

### 0536 — `.todos/DONE/0536-privacy-switches-on-their-pages.md`

- Share dialog: `keep_gps`, `long_side_px`, `quality` in the dialog, the default saved on
- `[review] lan` / `lan_phone_originals` shown as a state.

### 0538 — `.todos/DONE/0538-page-settings-import-events-slideshow-ai.md`

- Events page "split / merge more" (`merge_gap_hours`, `min_event_size`, `trip_min_km`)

### 0543 — `.todos/PARTIAL/PARTIAL_0543-mh-try-docker-run-first-port-check-on-failure.md`

- `mh --lan`: its "opening" / firewall lines are still said before the container starts

### 0545 — `.todos/DONE/0545-store-landmark-in-index-search-show-scan.md`

- `classify` still computes its towns: a trip's town is the largest town around a group's centre, and `folder_town` comes from the folder's name; neither is a fact of one photo, and reading the stored town would change the folders of existing sorts.
- The GPS line of the large view (`search/gps_town.py`), `album_reader`, `tags/place_words` still use the gazetteer.
- The other tile pages (import, quarantine, phone, reviews) show no place.
- The `{region}` placeholder of `[classify] layout` is kept although the regions are "never in folder names".
- The landmark and the town are computed once and stored; the slideshow and classify no longer recompute them
- Search finds a photo by its landmark or its town; tiles and large view show it
- A scan fills it for the existing GPS photos, offline; tests for moves/renames

### 0550 — `.todos/DONE/0550-tidy-config-toml-stale-entries.md`

- The web page with ticks (memory: visible in web or nonexistent).
- `[[classify.place_photos]]` line by line, town renames vs GeoNames, `people` files.
- A `path` rule aimed at a root the index never covered still looks stale when the index
- Every kind of the table detected, with tests (folder renamed, moved by `sort`, drive
- Nothing removed without being shown and ticked; backup copy; result read back
- Comments and order of `config.toml` kept (test on the default template)

### 0551 — `.todos/DONE/0551-one-photo-id-path-and-content-for-places-and-people.md`

- People faces as `{path, id, face}` in `people/*.toml` (still `<path>#<n>`), old form migration, relocation at audit.
- Relocation only runs at the end of the `audit` command, not in `import` nor the home-page audit.
- Wire change: the places page's take-back request sends `id` instead of `sha256` — to confirm.

### 0567 — `.todos/DONE/0567-read-only-steps-shown-in-the-page.md`

- `folders`: a host step (`Kind.HOST`, run by `mh.ps1` on Windows), the container cannot list it.
- The text is shown preformatted (Rich's plain export), not as a styled panel/table.

### 0572 — `.todos/DONE/0572-search-events-tab-without-a-classify-plan.md`

- Remove the plan-based UI now hidden (`events_choice`/`events_sure`/`events_rule`/
- Grid never stale under an event (test)
- Moved rows found by content; sorted-by-any-means counted (tests per move kind)
- Plan age shown, or the tab works without a plan (per the maintainer's choice)

### 0585 — `.todos/DONE/0585-intruders-page-home-link-and-dead-sidebar.md`

- *Back to the home page* on the page opened by a typed command (first acceptance line).
- The intruders page has *Back to the home page*, typed or opened from home
- No sidebar item looks clickable without being one, on any page (test)

### 0588 — `.todos/PARTIAL/PARTIAL_0588-people-page-opens-fast.md`

- New photos: the page opens at once, their analysis followed in it

### 0601 — `.todos/DONE/0601-page-undo-route.md`

- *Apply now* of the review pages, the people page and the other pages: their servers do not
- *Apply now* in its "applying" mode (the server ends, the home page opens): no toast.

### 0614 — `.todos/PARTIAL/PARTIAL_0614-tv-door-welcome-page.md`

- The line of index facts (photos, years covered).
- The *On this day* background.

### 0645 — `.todos/DONE/0645-local-ai-card-on-every-ai-page.md`

- Same card, same template, on each AI page — PARTIAL: the card is now one shared,

### 0655 — `.todos/DONE/0655-tv-button-on-every-tile-page-replaced-on-remote.md`

- 📺 on the other review pages with tiles (`unwanted_review`, `quarantine`, `import_pick`), on
- 📺 in the bar of each review page, `/person` and the phone page when a TV is paired (tests)
- Picked files, or nothing picked → the page's files, as on search
- The remote tells "replaced" after a selection replaced a running show (test)

### 0657 — `.todos/DONE/0657-albums-api-on-phone-and-person-pages.md`

- ➕ and 📺 in the bar of the phone page and `/person` (tests), picked or the page's files
- Keys resolved from the index only (a test with a forged path refused)

### 0661 — `.todos/DONE/0661-running-step-shown-on-every-page.md`

- The end message is *Done: <stage>.* / *Stopped (code n): <stage>.*: `/api/step` does not carry
- The chip, the title and the end toast on every page extending `page_frame.html.j2`

### 0664 — `.todos/DONE/0664-shared-busy-and-message-feedback.md`

- Pages with their own fetch helper, not migrated (each needs its own review of its status
- The Undo toast keeps its element (same look, same place, below the stack): merging it into
- Errors' sentence shape (what failed, what stays done, what to do) left to each server answer.
- The three pieces in the frame's templates, no page-specific copy (the test counting

### 0665 — `.todos/PARTIAL/PARTIAL_0665-library-bar-and-filters-grouped-in-menus.md`

- *to a folder* in Move ▾. **Reason:** no move-to-a-folder action exists on the page.
- *make from the results* / *link* in Album ▾: *📚 album of the results* stays in the left
- The browser cap (40) is an estimate until the first CI run prints the real count.
- The same menus, same order, on every tile page (the shared-parts test)
- Every action still reachable by its key; no action lost (a table old → new in the PR)
- The count of visible controls at load measured before / after, the cap in a test

### 0666 — `.todos/DONE/0666-page-view-kept-in-the-url.md`

- View keys of junk, gone, intruders, people, places, quarantine, shrink (their tab/filter):
- Other templates still read `URLSearchParams(location.search)` directly (person, quarantine,
- The helper is in the shared templates only

### 0667 — `.todos/DONE/0667-people-page-on-the-shared-frame.md`

- `mhBusy` on the section buttons (a save is short, the bar's *Saving…* line stays): left for
- `people.html.j2` extends `page_frame.html.j2`; no exception for it in the test

### 0669 — `.todos/DONE/0669-pages-accessibility-and-comfort-checks.md`

- Light `--mk-primary` on `--mk-n-50` is 4.42:1 (outline buttons on sunken chips): not
- The four checks run on every page of the walk, both themes; failures fixed or listed
- Reduced motion honoured by the frame (slideshow cross-fade included)

### 0671 — `.todos/DONE/0671-pages-csp-without-unsafe-inline-and-hostile-names.md`

- The hostile fixture in the demo tree (folder/file/EXIF/XMP/album/person/tag/place names)
- JSON answers are not checked with hostile data (served `application/json` + `nosniff`,
- The hostile fixture walk passes on every page, PC and phone doors
- No `'unsafe-inline'` in `script-src`; the places page's own policy included
- The lint over the 44 sites, exceptions named

### 0673 — `.todos/DONE/0673-thumbnails-cached-by-the-browser-across-runs.md`

- The other tile servers keep the per-run `ETag`: person, people, places, reviews, events
- Accepted limits (reviewer): a file replaced with the same size and mtime keeps its tag
- One test per invalidation event above
- Requests and bytes for a 200-tile page, second visit, before / after, in the PR

### 0675 — `.todos/DONE/0675-large-view-preloads-its-neighbours.md`

- The Events review's own code (`search_events_ahead.js.j2`) is kept: it preloads the next
- No preload on a phone using mobile data saver (`navigator.connection.saveData`)

### 0678 — `.todos/DONE/0678-page-speed-budget-on-a-synthetic-library.md`

- 300,000 files, the people routes: the first opening alone is estimated ≈ 250 s (×9
- The profile at 300,000: py-spy did not finish within 170 s there (its overhead on a
- No weekly CI job: the 100,000 run takes ≈ 2 min of CPU on a fast PC and the figures
- The table at 3 sizes; what grows faster than linearly is named, with a TODO each
- The helper documented in the devcontainer cheatsheet; runs gently (`nice`, 1 at a time)

### 0679 — `.todos/DONE/0679-dev-pages-reload-on-template-change.md`

- An open tab does not reload by itself after a template-only edit (no restart, so no new
- `dive_ci` not run (no file of the image changed, so the size is unchanged by construction).
- Edit a template → the open page shows it within 2 s, no key pressed
- `dive_ci` / the image size unchanged; `development.md` EN + FR

### 0683 — `.todos/DONE/0683-paired-devices-last-seen-expiry-and-activity.md`

- Flush of the activity counts at stop.
- TVs' `last_seen`: not written (`slideshow/screens.py` at 199 lines caches tokens in memory).
- The card lists name, paired on, last seen, address; rename and forget read back
- Expiry tested with a clock; *Forget all* tested
- What happens when `/lan` moves or is restored from an older copy: written and tested
- Docs EN + FR

### 0684 — `.todos/PARTIAL/PARTIAL_0684-guest-devices-see-chosen-albums-only.md`

- *Until tonight* (a guest pairing ending with the visit): guests last like a family phone and are
- The reports' hidden files (`.mh-*`) are still served to a family phone. **Reason:** decided

### 0687 — `.todos/PARTIAL/PARTIAL_0687-journals-and-choices-saved-off-the-pc.md`

- Point 2, a copy of the journal next to the quarantine (`<quarantine>/<run>/journal.jsonl`)
- The undo of a **sort** after backup → wipe → restore is not tested (only clean): the same
- A backup → wipe of `/journal` → restore → `undo` of a clean and of a sort works
- `undo --from-quarantine` on a run whose journal is gone: every file back, proven
- What happens when the quarantine moves to another drive letter: tested
- Docs EN + FR

### 0688 — `.todos/DONE/0688-quarantine-protected-until-purge.md`

- The figure on the quarantine page, the disk-space page and in `mh push`'s lines.
- A NAS copy counted as cover.
- The only copies are asked after the general purge question, not shown before it.
- The count of only-copy files shown before a purge, proven on the demo tree (a near
- With A: a push after a clean copies the run's quarantine; after a purge it leaves
- Docs EN + FR (`push.md`, `purge.md`, `reference-safety.md`)

### 0689 — `.todos/PARTIAL/PARTIAL_0689-are-my-photos-safe-card.md`

- **The restore drill (*Try now*)**: shown as "never tried", unknown, no button.
- **The NAS's own listing**: "files newer than the push" counts the index's files whose
- **The backup's off-PC check** reads the archive's Windows path: `mh` mounts `/backups`
- The card with real values on the demo tree in each state (no target, old push,

### 0690 — `.todos/PARTIAL/PARTIAL_0690-silent-corruption-detected-and-repaired.md`

- Web side: the safety card offer and a *Restore this one* page (the console path shows the
- A test flipping one byte of a demo photo keeping its mtime: found by the re-read,
- Docs EN + FR

### 0691 — `.todos/DONE/0691-settings-files-keep-their-previous-versions.md`

- The Undo toast after a settings save, Ctrl+Z, and the *Versions* page (date, short diff of
- `classify/remember_rule.py` rolls `config.toml` back with `write_bytes(before)` after a
- Index-only data (hand-typed tags, landmarks): covered by `mh backup` and the tag pages' own
- Every save path of the pages goes through the helper (a test lists the writers of
- Save → Undo → the file is byte-identical to before (test per file kind)
- The history never grows past its bound; restored and moved folders handled (tested)
- Docs EN + FR

### 0692 — `.todos/PARTIAL/PARTIAL_0692-home-page-ready-at-once-after-a-restart.md`

- Second start of `mh` (container removed, nothing changed): the home page is drawn
- The safety card shows the same facts as before (equivalence test), and follows each
- No traceback, no endless spinner if the card's route fails (message in the card)
- New strings through `_()` + French; both documentation languages if a capture changes

### 0694 — `.todos/PARTIAL/PARTIAL_0694-phone-page-served-by-the-home-server.md`

- The phone page is answered by the home server; no second server is started
- ▶ Slideshow ▾ › On the TV starts the chosen tiles on `/screen` (test)
- The way back home and *Apply now* are there, as on every set-aside page

## Status — PARTIAL (2026-11-12)

### Done
- Section 0339 (places map framing): its two unticked boxes were only a browser check. Now a
  Chromium walk, `tests/support/places_frame_walk.py`, run by
  `tests/e2e/test_ask_dialog_browser.py` (CI, `MEDIA_HYGIENE_E2E_BROWSER=1`): clusters in
  Paris, Brussels, Rome and one at 0, 0; on arrival at 1366 x 768 the three are on the
  visible map (left of the drawer), the 0, 0 one is not. Proven to fail when the 0, 0 filter
  of `frame()` is removed (measured: run in the devcontainer, 3 s). No product code changed:
  the framing of 0339 was right. `render_page` takes `given` values (real routes).

### Not done
- Every other section above.
  **Reason:** an index of ~40 sections; one focused session took one. Each section still needs
  its check against the code and, where work is real, its own focused TODO (see *How to use it*).
