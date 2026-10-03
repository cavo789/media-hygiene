# 0056 — Things to review: the maintainer's decisions and checks left by the PARTIAL TODOs

- **Priority**: High — eight PARTIAL TODOs and one BLOCKED wait on these answers
- **Batch**: review
- **Depends**: —
- **Files**: `.todos/PARTIAL/`, `.todos/BLOCKED/BLOCKED_0045-decode-heic-with-pi-heif.md`

## Context

The 2026-09-30 → 2026-10-03 sessions implemented the backlog with one sub-agent per TODO. Every
agent recorded the choices it made on its own and the checks it could not run (no Excel, no
Windows, no access to the real collection, Docker's attached output broken after a reboot). This
file gathers all of them in one place, so they can be answered progressively, and the PARTIAL
files closed one by one.

How to use it:
- Tick a box when it is answered or checked; write the answer on the line below it (`→ …`).
- When every box of a TODO is ticked, Claude applies the answers: a "keep" answer closes the
  PARTIAL file (moved to `DONE/` or `UNNEEDED/`); an answer that asks for work becomes a new TODO
  (`/todo` no longer reaches PARTIAL files).
- **Default** is what the code does today: leaving it as is means answering "keep the default".
- The second part lists choices already applied in DONE TODOs: only to confirm or change.

## Part 1 — Prerequisite

- [ ] **Restart Docker Desktop.** Since the PC reboot of 2026-10-02, `docker run` drops the
  attached output written more than ~1 s after start
  (`docker run --rm alpine sh -c 'sleep 3; echo late-output'` prints nothing).
  Then ask Claude to run, at low load, one step at a time:
  - [x] `e2e` once: not run since TODO 0029 although the image changed (0030, 0031, 0041, 0044,
    0005: new commands, new `ffmpeg` stage).
    → run by TODO 0057 on 2026-10-03: 5 passed.
  - [x] `docs_screenshots` (en, then fr): `config.txt` lacks `places.*` and `album.root`; the help
    blocks of `places`, `review-sort`, `album`, `undo`, `--tier` were filled by hand from the
    sources and must be confirmed.
    → run by TODO 0057 on 2026-10-03 (en and fr): every capture and help block regenerated.

## Part 2 — PARTIAL and BLOCKED TODOs

### 0027 — `classify` workbook and report

- [ ] Open a `classify.xlsx` in **Microsoft Excel**: no repair prompt; sheets and structure
  locked; only the yellow cells editable; filters and drop-downs work.
  → closes 0027.
- [ ] Decide how the documentation shows the workbook (same question as 0032 below).

### 0029 — `classify` with a local vision model

- [ ] Run `classify --sample 50` on the real collection, with a `subject` rule and your own
  categories; note in the PARTIAL file the seconds per photo and how many of the 50 subjects
  are right.
- [ ] From those figures: add `bge-m3` embeddings (or a CLIP fast pass) for the mapping step, or
  not? Default: not built.
- [ ] When the confirmation "describe N photos?" is refused, `classify` goes on with the cache
  only. Keep, or abort the whole run?
- [ ] The `subject` rule is commented out, low in the default rule list, with example
  categories. Keep its position and categories, or change them?

### 0030 — Places from GPS, the map page

- [ ] **Place from a folder name** (`2017/Bruges` → Bruges): ordinary folder words collide with
  real towns (Mons, Spa, Nice). Choose one: a population threshold · country names only · only
  aliases you list · an opt-in rule with a low score · not wanted.
- [ ] If wanted: its category is the folder's own label, or `{country}/{city}`?
- [ ] **Renaming towns** (GeoNames often gives English names: Turin, Munich, Brussels): add a
  table such as `[classify.town_names]`, or is the `trip` rule's category template enough?
- [ ] **Map page screenshot** in the docs: wanted (it fetches real OpenStreetMap tiles while the
  docs are generated, with a synthetic place), or text only?

### 0032 — Inventory export

- [ ] Open an `inventory.xlsx` in Excel: frozen header, filter, date and percent formats.
- [ ] **Workbook screenshots in the docs** (0027 and 0032): an HTML rendering of the first rows ·
  LibreOffice headless added to the docs tooling · one capture taken by hand in Excel · none.
- [ ] Check the default thresholds on the real collection: `[inventory] blurry_below = 100` and
  `clipped_above = 0.25` were guessed, not measured.
- [ ] Add the total video duration to the Summary sheet? Default: no.
- [ ] Re-read the French column headers ("Rubrique", "Ouverture (f/)", "Débit binaire").

### 0040 — Rename to media-hygiene (release 0.3.0)

- [ ] Publish 0.3.0: merge `sortering` into `main`, full `check`, then `release` (tag `v0.3.0`).
  Best done after Part 1 and after the security bump 0054 if `pillow-heif` 1.9.0 is out.
- [ ] Delete the Docker Hub repository `cavo789/media-dedup` once `cavo789/media-hygiene:0.3.0`
  is published.
- [ ] After the next clone under the new name: update the paths in `.claude/settings.json`.

### 0041 — Albums as hard links

- [ ] On Windows, in a **synthetic** folder (procedure in the PARTIAL file, e.g.
  `C:\Temp\links`): does `album … --apply` make true NTFS hard links through Docker Desktop
  (`fsutil hardlink list`)? Same question through a WSL `/mnt/c` path.
- [ ] If links fail on Docker Desktop: keep `album` for Linux/NAS users (it refuses cleanly), or
  remove it (UNNEEDED)?
- [ ] Album behaviour: flat folder, original names, additive (a photo no longer selected stays).
  Want a "sync" mode that removes it, or date-prefixed names for chronological order in
  Explorer?
- [ ] `--category` matches the category as `sort` would apply it (your renames included). Should
  it also match the originally proposed name?

### 0053 — The rare silent crash (exit 139)

- [ ] Do the WSL / PC restarts also happen outside this project, under any heavy Docker load?
  (Windows Event Viewer → System: Kernel-Power 41, WHEA, display driver; `mdsched.exe` memory test.)
- [ ] Follow the lead: import `pillow_heif` and `rawpy` lazily, only where pictures are decoded,
  so that `undo`, `history`… never load libheif/x265/LibRaw? (Also faster start-up.)
- [ ] Next time an e2e run fails: keep `/tmp/media-hygiene/e2e.log` and give it to Claude.

### 0009 — Immich as the family library

- [ ] Decide: (1) not now · (2) Immich as a read-only viewer over the sorted tree (recommended,
  once the disks are clean) · (3) Immich as the master library.
- [ ] Which machine would host it (Linux box, NAS, this Windows PC)?
- [ ] Do family members want the mobile app, automatic backup and sharing (reasons for option 3)?
- [ ] If option 2: a short trial with synthetic pictures first (hard links shown as duplicates,
  a moved file losing its album, on the current Immich release).

### 0045 (BLOCKED) — x265 (GPL) in the image

- [ ] `pi-heif` is discontinued. Choose: (1) keep `pillow-heif` and list x265 in the Docker Hub
  licence section · (2) build libheif + libde265 without x265 in a Dockerfile stage (no GPL,
  ~23 MB less, manual bumps on every security release) · (3) wait for another maintained
  decoder.

### 0054 (open) — `pillow-heif` 1.9.0

- [ ] Nothing to decide: run `/todo 0054` once `pillow-heif` 1.9.0 is on PyPI (libheif 1.23.5,
  one high-severity fix). Ideally before the 0.3.0 release.

## Part 3 — Choices already applied (DONE TODOs): confirm or change

- [ ] **0035 date rules:** a date rule takes an event when at least half of its files fall in the
  range (literal "overlaps the dates" would let a birthday swallow a whole trip). Keep?
- [ ] **0035 warning:** every rule that decided nothing is listed (5 of 6 default rules on the
  demo). Keep for all, or only for the rules you write (`date_range`, `path`, `camera`)?
- [ ] **0035 undated files** matched by a rule keep the reason `undated`, so the rule may be
  listed as "decided nothing". Credit them to the rule instead?
- [ ] **0036 carry-over source:** only the latest classify run's workbook (not older runs). Keep?
- [ ] **0036 cleared yellow cell:** a carried folder still applies at the next `sort` even if the
  pre-filled cell is emptied. Acceptable?
- [ ] **0036 notes** of events a sort fully applied are dropped. Fine?
- [ ] **0046 score** of a file kept in "To check" as a previous guess: `[classify] unsure` (50),
  not the rules' score. Fine?
- [ ] **0043:** `review` accepts `--exclude` but not `--exclude-name` nor `--ext`. Add them?
- [ ] **0005 tier:** re-encoded videos are quarantined by `clean --tier near`, like near-duplicate
  photos. Keep, or a separate tier value?
- [ ] **0005 date rule:** a video copy must have the original's date or none, so copies re-dated
  by messaging apps (WhatsApp…) are missed. Relax it (a later date on the smaller copy), knowing
  security-camera clips argue against?
- [ ] **0031 conflicts:** a workbook edit made after a choice on the `review-sort` page blocks
  `sort` until chosen again in one place (the TODO said "the page wins"). Keep, or the page
  always wins with a report?
- [ ] **0031 storage:** page choices in `sort-decisions.json` beside `plan.json`. OK?
- [ ] **0031 keys:** Enter accept, N/P next/previous, U, Shift+S event stays, ←/→ Space select,
  O send to a category, S photos stay, Delete take back, Z zoom, E/C fields (letters follow the
  keyboard layout, AZERTY included). Any clash with your habits?
- [ ] **0031 screenshot** of the page in `sort/10-name-events-in-the-browser.md`: add one with the
  docs scenario (after Part 1)?
- [ ] **0050:** two companion files edited to different folders make `sort` refuse the workbook;
  folder names are compared exactly (`Vacances` ≠ `vacances`). Keep case-sensitive?
- [ ] **0055 CSV:** text starting with `= + - @` gets a leading apostrophe in `plan.csv` and
  `inventory.csv` (Excel then computes nothing, but may show the apostrophe). Keep, or raw text?
- [ ] **0057 `--delete`:** immediate deletion is a `clean --delete` flag only, no `[clean]`
  setting (a config value would make deletion permanent unnoticed). Keep?
- [ ] **0057 empty files:** `clean` still deletes 0-byte files (nothing in them; `undo` recreates
  them) rather than quarantining them. Keep?
- [ ] **0057 albums:** after a later `sort` moved the original, `undo` of the album keeps the
  album's name (the recorded original is gone) and says why. Keep, or look the original up in
  the sort journals?
- [ ] **0057 tool folders:** a quarantine, journal, cache or reports folder inside (or around) a
  photo folder is refused (audit, classify, clean, sort, album, purge, `reports --prune`; never
  `undo`), unless it lies in `[folders] excluded`. Refuse, or only warn?
- [ ] **0057 console:** the 🔒 line and the `:ro` tip (with the safety page URL) print at every
  read-only run that reads the photos while a photo mount is writable. Too chatty?

## Part 4 — Checks on the Windows machine (DONE TODOs, untested here)

- [ ] **0028:** a `sort` between two different disks (cross-device move); Ctrl+C during a `sort`
  in `docker run -it`; Excel's lock file `~$classify.xlsx` detected while the workbook is open.
- [ ] **0038:** the `review` page names the decisions file as a `C:\…` path under Docker Desktop.
- [ ] **0039:** PowerShell 5.1: a decisions file / `config.toml` saved with `Set-Content
  -Encoding UTF8` (BOM) or `Out-File` (UTF-16) is read back.
- [ ] **0037:** the `X` key sets a whole burst series aside in a real browser.
- [ ] **0044:** one real search on the `places` page (OpenStreetMap / Nominatim) returns an area
  (only a fake server was used in tests).
- [ ] **0005:** real phone videos (WhatsApp re-encode, iPhone HEVC, 4K) are found as re-encoded
  copies.
- [ ] **0035:** on the real collection, PNG exports without EXIF are not taken for screenshots,
  and home videos named `720p`/`1080p` not for downloads.
- [ ] **0057:** a `sort` on one NTFS mount of Docker Desktop: renamed (instant) or copied file by
  file (`renameat2` unsupported there falls back to the verified copy: slower, same result)?
  And `-v "C:\Photos\quarantine:/quarantine"` next to `-v "C:\Photos:/data/c/Photos"` is refused.
- [ ] **0023, 0032:** re-read the new French wordings ("déplacées en quarantaine", inventory
  headers).

## Acceptance

- Every box is ticked, each with its answer.
- The PARTIAL files 0009, 0027, 0029, 0030, 0032, 0040, 0041, 0053 and BLOCKED 0045 are closed
  (DONE, UNNEEDED, or a new TODO for the work an answer created).
