# 0026 — `classify` engine: dates, folder names, events, calendar, ordered rules, confidence

- **Priority**: High
- **Batch**: classify
- **Depends**: 0025
- **Files**: `src/media_dedup/classify/` (new: `dates.py`, `folders.py`, `events.py`, `calendar.py`, `rules.py`, `layout.py`, `models.py`), `src/media_dedup/services/classify.py`, `src/media_dedup/cli/cmd_classify.py`, `src/media_dedup/cli/app.py`, `src/media_dedup/config/settings.py`, `src/media_dedup/config/templates/config.toml.j2`, `src/media_dedup/constants.py`, `documentation/en/`, `documentation/fr/`

## Context

Goal: propose a `year/category` tree for tens of thousands of photos and videos saved in one
folder per year, **without changing anything** (read-only command, `:ro` mounts accepted). The
proposal is then edited (0027) and applied by `sort` (0028). The verbs mirror `audit` / `clean`:
`classify` looks, `sort` acts; no `--dry-run`.

A real 70,000-photo family collection reshaped the design:
- **GPS: 1.3 %** of images. Geography from coordinates is a minor signal here (moved to 0030).
- **EXIF date: 90 %**, but several cameras had a wrong clock: a `2016/Juillet 2016` photo dated
  2011, a camera stuck on its factory year.
- **Folder names carry most of the meaning.** `Mars 2005 - Travaux maison`,
  `Décembre 2003 - Saint-Nicolas`, `2017/Janvier 2017/Bruges`, `Juin 2015/Kermesse`, or a
  top-level folder named after a person or a device (`<Name>/2018/…`).
- **The local vision model missed the occasion** on a Saint-Nicolas photo and a Christmas Eve
  photo (0029). The folder name and the calendar knew.

## Proposal

**Scan**: the same walk and index as `audit`. After an audit, `classify` decodes nothing.
- Excluded folders are not analysed.
- Protected folders are listed as "never moved".
- The target root is excluded from the scan automatically.
- Only media files are proposed. Other files stay where they are; count the folders they will
  keep from emptying.

**Date of each file**, the first reliable source wins; the source and a date confidence are
recorded:
1. EXIF `DateTimeOriginal` (+ `OffsetTimeOriginal`). Accept the non-standard formats seen in
   the wild (`DD/MM/YYYY hh:mm:ss`).
2. The video date (0025).
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
  confidence.
- A top-level person or device folder (`<Name>/2018/…`) gives the category `<Name>` under each
  photo's year.

**Events**: files sorted by date, cut where the gap exceeds `event_gap_hours`, across folders
(two phones at the same party). An event carries its span, count, folders, cameras, dominant
folder label and GPS when any. It is the unit that 0027 lets the user name once, and that 0029
samples for the AI.

**Calendar rules** (cheap, strong): configurable recurring dates → category, applied to the
events that overlap them.
- Defaults: Christmas 24–26/12, New Year 31/12–1/1, Saint-Nicolas 5–6/12.
- The user adds birthdays and any other date.

**Ordered rules** in `[[classify.rules]]`, first match above `sure` wins. Rule kinds:
- `existing_folder`;
- `calendar`;
- `kind`: document or screenshot from metadata (PNG without camera, screenshot name patterns,
  tiny images);
- `place` / `trip` (0030);
- `subject` (0029);
- the fallback `other_category`.

**Confidence**:
- Each proposal records a reason (`SortReason`, like `KeepReason`) and a score. Scores per
  reason come from a configurable table, never literals.
- Bands:
  - `≥ sure` → `sure_layout`;
  - `≥ unsure` → `unsure_layout` ("to check/<category>");
  - otherwise → `manual_layout`;
  - no date → `undated_layout`.
- "Other" means "sure nothing matches"; "manual" means "we do not know".

**Layouts**:
- Placeholders are validated at load time: `{year}`, `{quarter}` (a number: write `Q{quarter}`
  or `T{quarter}`), `{month}` (two digits), `{month_name}` (translated), `{day}`, `{category}`,
  `{place}`, `{country}`, `{region}`, `{city}`.
- Folder and category names are free text in any language, NFC-normalised, and checked for
  Windows-forbidden characters and names. `/` is the sub-folder separator.

**Default taxonomy**: it is an **example**, written in the generated `config.toml` in the
interface language, which each user replaces.
- Occasion- and activity-based: Parties (Christmas, Saint-Nicolas, New Year, birthdays),
  Holidays and outings, School, Sport and leisure, Home and works, Animals, Nature and
  landscapes, Documents and screenshots, Other.
- A comment warns against a "Family / portraits" category: in a family collection it swallows
  most photos (7 of 12 in the 0029 sample).

**Command**: `classify` prints a summary per year, band, category and reason. The files it
writes come with 0027.

## Acceptance

- [ ] Unit tests: date chain (each source, non-standard EXIF, patterns), clock check, generic vs
      meaningful folder names (fr/en/nl months), `Mois AAAA - Label`, events, calendar, rule
      order, bands, placeholders (unknown one refused with the allowed list), Windows names.
- [ ] Integration: `audit` then `classify` on a synthetic tree, **no decode** the second time
      (counting fake), `:ro` data mount accepted.
- [ ] Default `[classify]` section in the config template (fr + en values), documented as an
      example; arrays of tables documented as not overridable by environment variables.
- [ ] New guide page en + fr; `reference-commands.md`; `.po` translated.
