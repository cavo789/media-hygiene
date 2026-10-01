# 5. Review the proposal: the workbook and the report

[Documentation](../README.md) › Sorting, step 5 · 🇫🇷 [Français](../../fr/sort/05-review-the-proposal.md)

`classify` proposed a place for every file ([step 4](04-classify.md)). Before anything moves, you
correct that proposal where it is wrong, and you name what the tool could not name: a trip, a
party. Two windows side by side:

- **a workbook**, `classify.xlsx`, opened in Excel or LibreOffice: this is where you **edit**;
- **a report**, `report.html`, opened in your browser: this is where you **look** at the photos.

## Get the two files

Mount a reports folder, as for [the HTML reports](../clean/04-html-report.md):

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene classify
```

The end of the output says where the files are:

<!-- capture: classify.txt|Workbook to edit| -->
```text
✅ Workbook to edit: /reports/20261001-123749-classify/classify.xlsx
✅ Report with the photos: /reports/20261001-123749-classify/report.html
💡 Edit the yellow cells and save: nothing moves until 'sort'.
```

Each run writes a new folder, `<date>-classify`, with three files:

| File | What it is |
|---|---|
| `classify.xlsx` | The workbook you edit. |
| `report.html` | The report, with one page per year and the previews. |
| `plan.json` | The whole proposal, file by file. The workbook belongs to it: keep them together, and do not edit it. |

Without a reports folder, the proposal stays on screen only: a workbook edited in a folder the
container forgets would be lost work.

## The report: look at the photos

The first page gives the progress, the work left, the years, **where to start** (the events that
hold most of the work) and **the collection once sorted**: the proposed folders with their file
counts, before anything moves.

![The first page of the classify report: four counters (files, already in place, to check or to sort, events), a table of the years with links to their pages, the events where to start with their share of the work, then the proposed tree of folders with their file counts](../images/classify-report.webp)

Each year has its own page: tens of thousands of previews do not fit one page. It lists the
events first, **with the ids and the order of the workbook's Events sheet**, then the files
outside any event, grouped by proposed folder. Each group shows its dates, its files, the folders
they come from, the proposed folder and why, and up to 8 previews spread over its span. Click a
preview to open the file; *All the files* lists every one of them.

![A year page of the classify report: the event Seaside holidays with its id, 37 files of which 3 to check or to sort, the cumulated share of the work, the proposed folder 2019/Seaside holidays marked Sure, the three folders its photos come from, then eight previews spread over its days with their names and times, and a link to all the files](../images/classify-year.webp)

## The workbook: edit the yellow cells

Only the yellow cells can be changed; the rest is locked, so that a slip cannot break the file.
Every sheet has a free **Notes** column, for you: it is never read.

| Sheet | One row per | What you can change |
|---|---|---|
| Summary | — | Nothing: the progress, the files per band, year, category, reason and date source. |
| Categories | proposed category | **New name**: rename the category everywhere. **Confirm the files to check**: `yes` makes its "to check" files sure, at once. |
| Events | event | **Name**: the name of the event (`Italy 2023`), which becomes its folder. **Category**: the folder, chosen in the list or typed. |
| Files | photo or video | **Final folder**: the folder of this file, relative to the target (`2016/Kermesse`). |

**Start with the Events sheet.** It is a work list: the events that are not decided yet come
first, the largest first, and the column *Share of the work, cumulated* tells how much of the work
naming the rows above covers. Most of the time, naming the first ten rows settles most of the
collection: one name covers a few hundred photos. The events already decided (a folder you had
named, files already in place) come last.

A few rules:

- **The most precise edit wins**: a file's final folder, else its event's, else its category's.
- **Companions follow one folder**: a Live Photo (`IMG_1.HEIC` + `IMG_1.MOV`) or a RAW file and
  its JPEG have one row each, but move together. A final folder typed on **any** of their rows
  decides for all of them; two of their rows with different final folders are refused by `sort`,
  naming both cells ([step 7](07-sort.md#how-files-move)).
- **Your edit is sure**: a file you place yourself leaves the "to check" band.
- **(stay where it is)** is a value of every list: the file, the event or the category is left
  where it is.
- Folders are written relative to the target, with `/` or `\`: `2016/Kermesse`. A name Windows
  refuses, or a folder that climbs out of the target (`..`), is refused with its cell.
- Excel cannot sort locked cells: the sheets come already sorted in their most useful order. Use
  the **filters** of the header row to narrow a sheet down.
- Save the workbook where it is, with its name, in the `.xlsx` format.

## Improve the proposal without losing your work

Change a setting (`merge_gap_hours`, a rule of [step 6](06-write-down-what-you-know.md)), add
new photos, and run `classify` again: **your edits are carried over** to the new workbook. It
reads the workbook of the latest `classify` run, the one `sort` would apply, and fills the yellow
cells of the new one with what you typed, notes included:

```text
✅ 412 edits carried over from the workbook saved on 2 October 2026 at 14:32:
C:\Photos triées\reports\20261002-123210-classify\classify.xlsx
```

- **A file keeps its edit** even if it was renamed or moved meanwhile: it is recognised by its
  content (the SHA-256 of the audit), by its path only when the content is not known.
- **An event keeps its name** in the new event that holds most of its files. An event split in
  two gives its name to both parts, and `classify` says so.
- **A category keeps its new name** and its "confirm" as long as it is still proposed.
- A carried edit is yours: the file is sure, with the reason `carried-over`, and you can change
  the yellow cell again.
- **Nothing is dropped silently**: an edit whose file is gone, whose category is no longer
  proposed, or whose event merged with another named one, is listed on screen and in the report,
  to type again where it belongs.
- Edits a `sort` already applied are not carried: those files are in their place, and `classify`
  sees them there.

`--carry-over <workbook>` carries the edits of another workbook (a copy you kept, an older run);
`--no-carry-over` starts fresh. A workbook `sort` refuses (a column deleted, a sheet renamed) is
still read, as far as its ids and yellow cells can be found: running `classify` again is the way
out. If the latest workbook cannot be opened at all, `classify` stops before writing anything, so
that your edits are not buried under a newer, empty workbook.

Nothing moves yet: applying the workbook to your folders is the job of `sort`
([step 7](07-sort.md)). It checks the workbook again before moving anything: a workbook of another
run, or one whose rows, sheets or locked cells were changed, is refused.

---

← [4. Propose a tidy tree](04-classify.md) · [Documentation](../README.md) · Next: **[6. Write down what you know](06-write-down-what-you-know.md)** →
