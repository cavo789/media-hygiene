# 0026 — `classify` engine: dates, folder names, events, layouts, bands (rules in 0035)

- **Priority**: High
- **Batch**: classify
- **Depends**: 0025, 0034
- **Files**: `src/media_hygiene/classify/` (new: `dates.py`, `folders.py`, `events.py`, `layout.py`, `bands.py`, `models.py`), `src/media_hygiene/services/classify.py`, `src/media_hygiene/cli/cmd_classify.py`, `src/media_hygiene/cli/app.py`, `src/media_hygiene/config/settings.py`, `src/media_hygiene/config/templates/config.toml.j2`, `src/media_hygiene/constants.py`, `documentation/en/sort/`, `documentation/fr/sort/`, `tests/support/docs/`

## Context

Goal: propose a tree (by default `year/category`) for tens of thousands of photos and videos
saved in one folder per year, **without changing anything** (read-only command, `:ro` mounts
accepted). The proposal is then edited (0027) and applied by `sort` (0028). The verbs mirror
`audit` / `clean`: `classify` looks, `sort` acts; no `--dry-run`.

Split on 2026-09-29: the ordered rules, the calendar and the example taxonomy moved to 0035.
The engine must stand without them: dates and folder names alone decide a large part of a
family collection, and a `{year}/{month}` layout needs no rule at all.

A real 70,000-photo family collection shaped the design:
- **GPS: 1.3 %** of images. Geography from coordinates is a minor signal here (0030).
- **EXIF date: 90 %**, but several cameras had a wrong clock: a `2016/Juillet 2016` photo dated
  2011, a camera stuck on its factory year.
- **Folder names carry most of the meaning.** `Mars 2005 - Travaux maison`,
  `Décembre 2003 - Saint-Nicolas`, `2017/Janvier 2017/Bruges`, `Juin 2015/Kermesse`, or a
  top-level folder named after a person or a device (`<Name>/2018/…`).
- **The local vision model missed the occasion** on a Saint-Nicolas photo and a Christmas Eve
  photo (0029). The folder name and the calendar knew.

Compared on 2026-09-29 with [sorta](https://github.com/shinKatana0/sorta), a local tool that
sorts by city, person or event (tested on 38,485 files). Its measured lessons are marked
*(sorta)* below: two-level event cutting, a minimum event size, and undated files split by
camera trace.

## Principles (every sort TODO: 0026–0031, 0035, 0036)

Sorting tens of thousands of photos is hours of tedious work. The tool removes the tedium; it
never takes the decisions away from the user.

1. **The user decides the structure.** Layout, taxonomy and calendar are examples the user
   replaces; nothing is hard-coded. Someone who only wants `year/month` needs no taxonomy.
2. **Nothing moves unseen.** `classify` is read-only; `sort` applies a plan the user had in hand.
3. **A guess never passes for a certainty.** Every proposal carries its reason and its band;
   "stay where it is" is always a valid answer, at every level.
4. **Human work is never lost**: edits carried over to the next proposal (0036), every move
   undoable (0024).
5. **Small batches.** A year, an event: each pass leaves the collection consistent, and running
   `classify` again after a `sort` is safe and proposes nothing new (idempotence).
6. **Spend the user's time where it pays**: the largest undecided events first.

## Proposal

**Scope and scan**: the same walk and index as `audit`. After an audit, `classify` decodes
nothing.
- Excluded folders are not analysed. Protected folders are listed as "never moved".
- **Folders to leave as they are** (`[classify] leave`, `--leave`): analysed, cleaned by
  `clean` like any other, but never moved by `sort` (a hand-made album, a scan project). Three
  distinct wishes, three settings: *not analysed* (`excluded`), *never modified* (`protected`),
  *not sorted* (`leave`).
- **The target root** (`[classify] target`, `--target`) is either a separate folder
  (`C:\Photos triées`) **or the source itself** (`C:\Photos` reorganised in place, the likely
  case for a collection saved as one folder per year). The target is scanned like any source:
  a file already at a place the layout accepts is **in place** and gets no move.
- `--year 2016` or `--year 2015-2017`: only the files dated in that range get a proposal; the
  others are left out of the outputs. One year per evening is how tens of thousands of photos
  become bearable.
- Only media files are proposed. Other files stay where they are; count the folders they will
  keep from emptying.
- **Duplicates first**: exact duplicates still in the index would be sorted twice (the second
  renamed ` (2)` by 0028). The summary counts them and tips `clean`; it does not refuse.

**Date of each file**, the first reliable source wins; the source and a date confidence are
recorded:
1. EXIF `DateTimeOriginal` (+ `OffsetTimeOriginal`). Accept the non-standard formats seen in
   the wild (`DD/MM/YYYY hh:mm:ss`).
2. The video date (0025), **converted to local time**: with the offset of the tag when it has
   one, otherwise with `[classify] timezone` (IANA name; default the container's `TZ`, else UTC
   with a warning). QuickTime's `creation_time` is UTC: 00:30 on 1 January is 23:30 on
   31 December, another year.
3. The file name, through configurable patterns with named groups: `IMG_20210712_…`,
   `20171224_110305`, `IMG-20210712-WA0001`, `PXL_…`, `Screenshot_…`, `2018-01-11_19h06_34`.
4. The folder: year folder, `Juillet 2017`, `2019-04`, `Mois AAAA - Label`.
5. mtime, last resort, flagged as weak.

**Camera clock check**: per camera (EXIF make + model), compare the EXIF year with the folder
year wherever both exist.
- A camera that disagrees most of the time is marked "clock not set": its folder dates win,
  and the reason says so.
- Any single disagreement lowers the date confidence, which sends the file to the "to check"
  band.

**Folder names**:
- **Date-only names are generic** for sorting: a year, month names in fr/en/nl, `YYYY-MM`,
  `Month YYYY`. Configurable patterns extend `keep.generic_folders`. Otherwise
  `2017/Juillet 2017` would be "kept as is" and nothing would be sorted.
- `Mois AAAA - Label` yields `Label`.
- A meaningful folder is **kept as is** under the photo's year: signal `existing-folder`, high
  confidence. Its sub-folders come along: `2017/Janvier 2017/Bruges/Jour 1` →
  `2017/Bruges/Jour 1`.
- A top-level person or device folder (`<Name>/2018/…`) gives the category `<Name>` under each
  photo's year.
- **The tool's own folders are never meaningful**: the names the layouts give to the "to check",
  "manual" and "undated" bands are generic automatically. Otherwise a second `classify` would
  keep `2016/À vérifier/Vacances` "as is" forever.

**Events**: files sorted by date, across folders (two phones at the same party), cut in two
levels *(sorta)*:
- a **session** ends where the gap exceeds `session_gap_hours` (default 6);
- sessions closer than `merge_gap_hours` (default 18) form one **event**: the evening and the
  next morning of one outing stay together, where a single gap would cut every trip at night.
  Joining the sessions of a trip over several days by GPS distance is 0030's job;
- groups smaller than `min_event_size` (default 5) are **not events**: their files fall back
  to their month (`{event}` renders as `YYYY-MM`). Otherwise "to sort" would hold hundreds of
  folders of one or two photos.

An event carries its span, count, folders, cameras, dominant folder label and GPS when any. It
is the unit that 0027 lets the user name once, and that 0029 samples for the AI.
- **Stable id**: derived from its earliest file's identity and its start, so that 0027, 0031
  and 0036 can match an event across runs.
- **One event, one year**: an event takes the year of its start (`event_year = "start"`, or
  `"per_file"`). A New Year's Eve party stays in one folder; so does a meaningful folder that
  spans two years.
- **Event neighbours**: the loose files of an event (date-only or generic folder) whose other
  files sit in one meaningful folder join that folder (reason `event-neighbour`, lower score than
  `existing-folder`). One phone saved the party in `Anniversaire Léa`, the other in `DCIM`. The
  same mechanism files next month's phone import into an event folder already sorted.

**Confidence**:
- Each proposal records a reason (`SortReason`, like `KeepReason`) and a score. Scores per
  reason come from a configurable table, never literals.
- Bands:
  - `≥ sure` → `sure_layout`;
  - `≥ unsure` → `unsure_layout` ("to check/<category>");
  - otherwise → `manual_layout`;
  - no date → `undated_layout`.
- **The band depends on what the layout needs**: without `{category}` in the layout, a reliable
  date is enough to be sure. `{year}/{month}` sorts most of a collection at once, with no
  taxonomy and no rule.
- Until 0035, loose files without a signal fall in the manual band.

**Layouts**:
- Placeholders are validated at load time: `{year}`, `{quarter}` (a number: write `Q{quarter}`
  or `T{quarter}`), `{month}` (two digits), `{month_name}` (translated), `{day}`, `{category}`,
  `{event}` (the event's name when it has one — its folder label, or the name given in 0027 /
  0031 — else its span, `2016-07-01..07-15` or `2016-07-14` for one day *(sorta)*),
  `{event_start}`, `{place}`, `{country}`,
  `{region}`, `{city}`.
- **An empty layout means "stay where it is"**, valid for every band.
- **Decided 2026-09-29**: the uncertain files are **gathered**, so that the user reviews them in
  the file explorer, with its thumbnails. Defaults, written in the interface language of the
  generated `config.toml`:

  | Band | fr | en |
  |---|---|---|
  | to check | `{year}/À vérifier/{category}` | `{year}/To check/{category}` |
  | manual | `{year}/À trier/{event}` | `{year}/To sort/{event}` |
  | undated, with a camera trace (make, model or GPS) | `À trier/Sans date` | `To sort/Undated` |
  | undated, no camera trace at all | `À trier/Reçues et téléchargées` | `To sort/Received and downloaded` |

  "Undated" means only the mtime is known: the year is not trusted. The split by camera
  trace comes from sorta: 1,057 of its 1,059 undated files had none and were messaging-app
  cache; the 2 others were real shots with a lost date. The folder name is not a verdict:
  forwarded pictures are often worth a look.

  - One sub-folder per event in "to sort": thousands of loose files in one folder cannot be
    reviewed. Renaming `2016/À trier/2016-07-14` to `Kermesse` in the explorer is a decision:
    the name becomes meaningful, and the next `classify` + `sort` files it as
    `2016/Kermesse`.
  - The band folders of **both** languages stay generic even after the user renames them in
    the configuration: an old `À vérifier` left on disk is never "kept as is".
  - "Stay where it is" (empty layout) remains one line of configuration away.
- `--layout "{year}/{month} - {month_name}"` on the command line, for the simplest use.
- Folder and category names are free text in any language, NFC-normalised, and checked for
  Windows-forbidden characters and names. `/` is the sub-folder separator.

**Command**: `classify` prints, in this order:
1. **Progress**: files already in place, count and share. After a few `sort` runs, this is how
   far the collection is.
2. A summary per year, band, reason and category.
3. **The work left**: "to check: N files in M events; the 20 largest events hold K of them".
4. The duplicates tip when exact duplicates remain.

The files it writes come with 0027.

## Acceptance

- [ ] Unit tests: date chain (each source, non-standard EXIF, patterns), video UTC → local
      time across midnight on 31/12, clock check, generic vs meaningful folder names (fr/en/nl
      months), `Mois AAAA - Label`, sub-folders kept, own band folders generic, `leave`
      folders, sessions merged over one night, groups below `min_event_size` falling back to
      their month, one event one year, event neighbours, undated split by camera trace, bands
      with and without `{category}`, empty layout, placeholders (unknown one refused with the
      allowed list), Windows names.
- [ ] Integration: `audit` then `classify` on a synthetic tree, **no decode** the second time
      (counting fake), `:ro` data mount accepted, in-place target, `--year` scope.
- [ ] Idempotence: a tree already in the layout's shape → nothing to move, 100 % in place.
- [ ] Default `[classify]` section in the config template (fr + en values), documented as an
      example.
- [ ] First page of the sort guide (`documentation/<lang>/sort/`, 0034) en + fr, with a demo
      library of synthetic year folders and dated EXIF (`tests/support/docs/`);
      `reference-commands.md`; `.po` translated.
