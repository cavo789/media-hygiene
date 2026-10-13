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

## Progress (2026-10-12)

Parts 1–3 answered; PARTIAL 0009 (→ UNNEEDED), 0027, 0029, 0030, 0032, 0040, 0041, 0053 and
BLOCKED 0045 closed, the work their answers created filed as TODOs 0114–0125. Left: the
Windows checks of Part 4: 0028 and 0057 done on 2026-10-14 (work filed as TODO 0138); 0005
(postponed) and 0035 still unticked.

## Part 1 — Prerequisite

- [x] **Restart Docker Desktop.** Since the PC reboot of 2026-10-02, `docker run` drops the
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
  → done: TODO 0057 ran `e2e` and `docs_screenshots` on 2026-10-03.

## Part 2 — PARTIAL and BLOCKED TODOs

### 0027 — `classify` workbook and report

- [x] Open a `classify.xlsx` in **Microsoft Excel**: no repair prompt; sheets and structure
  locked; only the yellow cells editable; filters and drop-downs work.
  → closes 0027.
  → 2026-10-12 (`mh classify --year 2015`, real collection): every white cell locked, every
    yellow cell writable; no repair prompt; filters and drop-downs work; sheets cannot be
    renamed, deleted or added.
    Asked: editable cells in pastel green → TODO 0116, then kept yellow (UNNEEDED, 2026-10-13). Console findings of the
    same run → TODO 0114 (subject lines) and 0115 (raw reason codes, untitled category rows,
    55-rule warning under `--year`).
- [x] Decide how the documentation shows the workbook (same question as 0032 below).
  → no screenshot (see 0032).

### 0029 — `classify` with a local vision model

- [x] Run `classify --sample 50` on the real collection, with a `subject` rule and your own
  categories; note in the PARTIAL file the seconds per photo and how many of the 50 subjects
  are right.
  → 2026-10-12, real collection, 26 path rules + calendar/place rules above `subject`, 7
    categories (Fêtes added): 506 events left to the model, 919 photos; 2.1 s describe + 0.2 s
    map per photo, a full run ≈ 34 min (the first estimate said 1 h 08: a default figure, not
    the last measure). 11 of 50 answered "none". "Maison et travaux" catches indoor family
    scenes (meals, sofa, Wii). Checked by the maintainer: descriptions very good; categories
    weak, 7 wrong of the 10 categorised photos checked (5 home scenes as "Maison et travaux", a
    family meal at the grandparents' as "Vacances et sorties", Santa hats in a September garden
    as "Fêtes"). Cause: `map.txt` gives the model category names only, no definition.
  → Decided: describe in French when `locale = fr` (descriptions were English by design,
    surprising in the `--sample` table): a new TODO.
- [x] From those figures: add `bge-m3` embeddings (or a CLIP fast pass) for the mapping step, or
  not? Default: not built.
  → no vectors (they would keep the same word confusion). Instead, new TODO: a definition per category (`"Name = definition"`, the definition sent to the mapping model only), and the default example "Maison et travaux" renamed "À la maison" (config template + docs).
- [x] When the confirmation "describe N photos?" is refused, `classify` goes on with the cache
  only. Keep, or abort the whole run?
  → keep: go on with the cache only.
- [x] The `subject` rule is commented out, low in the default rule list, with example
  categories. Keep its position and categories, or change them?
  → keep the position; categories kept except "Maison et travaux" → "À la maison" (above).

### 0030 — Places from GPS, the map page

- [x] **Place from a folder name** (`2017/Bruges` → Bruges): ordinary folder words collide with
  real towns (Mons, Spa, Nice). Choose one: a population threshold · country names only · only
  aliases you list · an opt-in rule with a low score · not wanted.
  → a population threshold with guards: the folder name equals the town's name exactly; towns
    in the countries of the collection's GPS photos first; ignored when the folder's own GPS
    photos contradict it; low threshold (5,000); low score, any other rule wins. GeoNames data
    shows a threshold alone fails both ways (Nice 342k, Paradise US 223k, Mons 95k vs Durbuy,
    Spa 10k; `Bruges` is Bruges FR 12k, Belgian Bruges is listed as `Brugge`). A new TODO.
- [x] If wanted: its category is the folder's own label, or `{country}/{city}`?
  → `{country}/{city}`, like the `trip` rule.
- [x] **Renaming towns** (GeoNames often gives English names: Turin, Munich, Brussels): add a
  table such as `[classify.town_names]`, or is the `trip` rule's category template enough?
  → add a `[classify.town_names]` table: a new TODO.
- [x] **Map page screenshot** in the docs: wanted (it fetches real OpenStreetMap tiles while the
  docs are generated, with a synthetic place), or text only?
  → wanted: a new TODO (synthetic place, real OSM tiles while the docs are generated).

### 0032 — Inventory export

- [x] Open an `inventory.xlsx` in Excel: frozen header, filter, date and percent formats.
  → checked 2026-10-12 on the real collection: no repair prompt, frozen header, filters, date formats right.
- [x] **Workbook screenshots in the docs** (0027 and 0032): an HTML rendering of the first rows ·
  LibreOffice headless added to the docs tooling · one capture taken by hand in Excel · none.
  → none.
- [x] Check the default thresholds on the real collection: `[inventory] blurry_below = 100` and
  `clipped_above = 0.25` were guessed, not measured.
  → checked 2026-10-12 on samples of the real collection: blurry, bright and dark files deserve their mark. Keep 100 / 0.25.
- [x] Add the total video duration to the Summary sheet? Default: no.
  → no.
- [x] Re-read the French column headers ("Rubrique", "Ouverture (f/)", "Débit binaire").
  → OK as they are.

### 0040 — Rename to media-hygiene (release 0.3.0)

- [x] Publish 0.3.0: merge `sortering` into `main`, full `check`, then `release` (tag `v0.3.0`).
  Best done after Part 1 and after the security bump 0054 if `pillow-heif` 1.9.0 is out.
  → tag `v0.3.0` pushed on 2026-10-03.
- [x] Delete the Docker Hub repository `cavo789/media-dedup` once `cavo789/media-hygiene:0.3.0`
  is published.
  → deleted by the maintainer.
- [x] After the next clone under the new name: update the paths in `.claude/settings.json`.
  → reminder kept in the closing note of DONE_0040; nothing to do until such a clone.

### 0041 — Albums as hard links

- [x] On Windows, in a **synthetic** folder (procedure in the PARTIAL file, e.g.
  `C:\Temp\links`): does `album … --apply` make true NTFS hard links through Docker Desktop
  (`fsutil hardlink list`)? Same question through a WSL `/mnt/c` path.
  → yes, both (2026-10-12, `C:\Temp\links`): `os.link` in the image through `-v "C:\Temp\links:/t"` and through `-v /mnt/c/Temp/links:/t` gives one inode for both names, `st_nlink` 2; `fsutil hardlink list` lists both names. True NTFS hard links.
- [x] If links fail on Docker Desktop: keep `album` for Linux/NAS users (it refuses cleanly), or
  remove it (UNNEEDED)?
  → not applicable: links work; `album` stays.
- [x] Album behaviour: flat folder, original names, additive (a photo no longer selected stays).
  Want a "sync" mode that removes it, or date-prefixed names for chronological order in
  Explorer?
  → keep: flat folder, original names, additive.
- [x] `--category` matches the category as `sort` would apply it (your renames included). Should
  it also match the originally proposed name?
  → keep: only the category as `sort` applies it.

### 0053 — The rare silent crash (exit 139)

- [x] Do the WSL / PC restarts also happen outside this project, under any heavy Docker load?
  (Windows Event Viewer → System: Kernel-Power 41, WHEA, display driver; `mdsched.exe` memory test.)
  → no, only with this project: the code lead stays open (lazy imports, new TODO).
- [x] Follow the lead: import `pillow_heif` and `rawpy` lazily, only where pictures are decoded,
  so that `undo`, `history`… never load libheif/x265/LibRaw? (Also faster start-up.)
  → yes: a new TODO.
- [x] Next time an e2e run fails: keep `/tmp/media-hygiene/e2e.log` and give it to Claude.
  → standing instruction, noted (the `e2e` helper writes that log).

### 0009 — Immich as the family library

- [x] Decide: (1) not now · (2) Immich as a read-only viewer over the sorted tree (recommended,
  once the disks are clean) · (3) Immich as the master library.
  → (1) not now: 0009 closes; revisit once the disks are clean and sorted (sort before any Immich import).
- [x] Which machine would host it (Linux box, NAS, this Windows PC)?
  → not applicable (not now).
- [x] Do family members want the mobile app, automatic backup and sharing (reasons for option 3)?
  → not applicable (not now).
- [x] If option 2: a short trial with synthetic pictures first (hard links shown as duplicates,
  a moved file losing its album, on the current Immich release).
  → not applicable (not now).

### 0045 (BLOCKED) — x265 (GPL) in the image

- [x] `pi-heif` is discontinued. Choose: (1) keep `pillow-heif` and list x265 in the Docker Hub
  licence section · (2) build libheif + libde265 without x265 in a Dockerfile stage (no GPL,
  ~23 MB less, manual bumps on every security release) · (3) wait for another maintained
  decoder.
  → (1): keep `pillow-heif`, list x265 (GPL) in the licence section.

### 0054 (open) — `pillow-heif` 1.9.0

- [x] Nothing to decide: run `/todo 0054` once `pillow-heif` 1.9.0 is on PyPI (libheif 1.23.5,
  one high-severity fix). Ideally before the 0.3.0 release.
  → done (`DONE/DONE_0054-…`).

## Part 3 — Choices already applied (DONE TODOs): confirm or change

- [x] **0035 date rules:** a date rule takes an event when at least half of its files fall in the
  range (literal "overlaps the dates" would let a birthday swallow a whole trip). Keep?
  → keep.
- [x] **0035 warning:** every rule that decided nothing is listed (5 of 6 default rules on the
  demo). Keep for all, or only for the rules you write (`date_range`, `path`, `camera`)?
  → keep.
- [x] **0035 undated files** matched by a rule keep the reason `undated`, so the rule may be
  listed as "decided nothing". Credit them to the rule instead?
  → keep.
- [x] **0036 carry-over source:** only the latest classify run's workbook (not older runs). Keep?
  → keep.
- [x] **0036 cleared yellow cell:** a carried folder still applies at the next `sort` even if the
  pre-filled cell is emptied. Acceptable?
  → keep.
- [x] **0036 notes** of events a sort fully applied are dropped. Fine?
  → keep.
- [x] **0046 score** of a file kept in "To check" as a previous guess: `[classify] unsure` (50),
  not the rules' score. Fine?
  → keep.
- [x] **0043:** `review` accepts `--exclude` but not `--exclude-name` nor `--ext`. Add them?
  → add them: a new TODO.
- [x] **0005 tier:** re-encoded videos are quarantined by `clean --tier near`, like near-duplicate
  photos. Keep, or a separate tier value?
  → keep.
- [x] **0005 date rule:** a video copy must have the original's date or none, so copies re-dated
  by messaging apps (WhatsApp…) are missed. Relax it (a later date on the smaller copy), knowing
  security-camera clips argue against?
  → keep.
- [x] **0031 conflicts:** a workbook edit made after a choice on the `review-sort` page blocks
  `sort` until chosen again in one place (the TODO said "the page wins"). Keep, or the page
  always wins with a report?
  → keep.
- [x] **0031 storage:** page choices in `sort-decisions.json` beside `plan.json`. OK?
  → keep.
- [x] **0031 keys:** Enter accept, N/P next/previous, U, Shift+S event stays, ←/→ Space select,
  O send to a category, S photos stay, Delete take back, Z zoom, E/C fields (letters follow the
  keyboard layout, AZERTY included). Any clash with your habits?
  → keep.
- [x] **0031 screenshot** of the page in `sort/11-name-events-in-the-browser.md`: add one with the
  → keep.
  docs scenario (after Part 1)?
  → no.
- [x] **0050:** two companion files edited to different folders make `sort` refuse the workbook;
  folder names are compared exactly (`Vacances` ≠ `vacances`). Keep case-sensitive?
  → keep.
- [x] **0055 CSV:** text starting with `= + - @` gets a leading apostrophe in `plan.csv` and
  `inventory.csv` (Excel then computes nothing, but may show the apostrophe). Keep, or raw text?
  → keep.
- [x] **0057 `--delete`:** immediate deletion is a `clean --delete` flag only, no `[clean]`
  setting (a config value would make deletion permanent unnoticed). Keep?
  → keep.
- [x] **0057 empty files:** `clean` still deletes 0-byte files (nothing in them; `undo` recreates
  them) rather than quarantining them. Keep?
  → keep.
- [x] **0057 albums:** after a later `sort` moved the original, `undo` of the album keeps the
  album's name (the recorded original is gone) and says why. Keep, or look the original up in
  the sort journals?
  → keep.
- [x] **0057 tool folders:** a quarantine, journal, cache or reports folder inside (or around) a
  photo folder is refused (audit, classify, clean, sort, album, purge, `reports --prune`; never
  `undo`), unless it lies in `[folders] excluded`. Refuse, or only warn?
  → keep.
- [x] **0057 console:** the 🔒 line and the `:ro` tip (with the safety page URL) print at every
  read-only run that reads the photos while a photo mount is writable. Too chatty?
  → keep.

## Part 4 — Checks on the Windows machine (DONE TODOs, untested here)

- [x] **0028:** a `sort` between two different disks (cross-device move); Ctrl+C during a `sort`
  in `docker run -it`; Excel's lock file `~$classify.xlsx` detected while the workbook is open.
  → 2026-10-14 (image 0.3.0, `C:\Temp\sort-test`, target on a second `-v`): cross-mount move
    copied and verified; Ctrl+C at 112/414 stopped cleanly (no traceback, "Nothing lost: 420
    files", 114 of 114 moves verified, resume and undo hints); src 300 + sorted 120 = 420; the
    rerun counted "Moved by an earlier run: 114"; `undo` brought the 114 back, 0 failed.
    Excel open on the workbook: `~$classify.xlsx` is there and `sort` warns ("open in Excel or
    LibreOffice: what is not saved is not read", tip: save, close, run again), then still asks
    (default No). Decided: keep the warning, no refusal (nothing is lost; an orphan lock file
    after an Excel crash would otherwise block `sort`).
    Unexplained: 6 files already sat in `sorted` before the interrupted run (most likely an
    earlier run stopped after 6 files); the test folder, journal included, was deleted before
    `history` could tell. The before/after count held (420), nothing to file unless it recurs.
    Seen in passing: the 0.3.0 tip printed "list it in  excluded" (Rich ate `[folders]`),
    already fixed on main (`cli/error_view.py` escapes the tip).
- [x] **0038:** the `review` page names the decisions file as a `C:\…` path under Docker Desktop.
  → checked 2026-10-12: console and page footer both say `C:\Users\…\media-hygiene\reports\decisions.json`.
- [x] **0039:** PowerShell 5.1: a decisions file / `config.toml` saved with `Set-Content
  -Encoding UTF8` (BOM) or `Out-File` (UTF-16) is read back.
  → checked 2026-10-12 in Windows PowerShell 5.1: a `config.toml` written by `Set-Content -Encoding UTF8` (BOM) and by `Out-File` (UTF-16) is read, same value both times. Piped through `Select-String`, PS 5.1 decodes the UTF-8 output with the OEM code page (`├Ç v├®rifier`, `Ôöé`): a console display matter, see 0098.
- [x] **0037:** the `X` key sets a whole burst series aside in a real browser.
  → checked 2026-10-12 in a real browser: X sets the whole series aside, A takes it all back; → keeps both (the default).
- [x] **0044:** one real search on the `places` page (OpenStreetMap / Nominatim) returns an area
  (only a fake server was used in tests).
  → checked 2026-10-12: a search by name on the `places` page drew the area (Nominatim).
- [ ] **0005:** real phone videos (WhatsApp re-encode, iPhone HEVC, 4K) are found as re-encoded
  copies.
  → postponed by the maintainer (2026-10-14). Procedure ready: three originals (Android, iPhone
    HEVC `.MOV`, 4K) and their WhatsApp received copies in `C:\Temp\video-test\videos`, `audit`
    with `:ro`; expect 3 groups under *Re-encoded videos*; for a miss, `ffprobe` duration and
    `creation_time` of both files.
- [ ] **0035:** on the real collection, PNG exports without EXIF are not taken for screenshots,
  and home videos named `720p`/`1080p` not for downloads.
- [x] **0057:** a `sort` on one NTFS mount of Docker Desktop: renamed (instant) or copied file by
  file (`renameat2` unsupported there falls back to the verified copy: slower, same result)?
  And `-v "C:\Photos\quarantine:/quarantine"` next to `-v "C:\Photos:/data/c/Photos"` is refused.
  → 2026-10-14, synthetic copy (`C:\Temp\sort-test`, 420 files, 3.0 GB, one mount, target inside
    it): **copied file by file**, ~70 s; `undo` copies back too (1 min 01 s, 420 back, 0 failed).
    Probe in the image on that mount: `renameat2(RENAME_NOREPLACE)` → `EINVAL`; `os.link` +
    `unlink` works and keeps the inode (11258999068581133), plain `rename` too. So a hard link then
    unlink would move instantly while still refusing an existing target: TODO 0138. The docs'
    "on one disk, a move is a rename: nothing is copied" is wrong under Docker Desktop.
    A quarantine mounted inside the photo folder is refused with a clear message and tip.
- [x] **0023, 0032:** re-read the new French wordings ("déplacées en quarantaine", inventory
  headers).
  → OK as they are.

## Acceptance

- Every box is ticked, each with its answer.
- The PARTIAL files 0009, 0027, 0029, 0030, 0032, 0040, 0041, 0053 and BLOCKED 0045 are closed
  (DONE, UNNEEDED, or a new TODO for the work an answer created).
