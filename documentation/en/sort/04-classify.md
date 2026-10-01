# 4. Propose a tidy tree: `classify`

[Documentation](../README.md) › Sorting, step 4 · 🇫🇷 [Français](../../fr/sort/04-classify.md)

Steps 1 to 3 showed what your folders hold. `classify` goes one step further: for every photo and
video, it proposes a place in a tidy tree, `year/category` by default. It **only proposes**:
nothing moves, and folders mounted `:ro` are fine.

> 💡 Clean the duplicates first ([the clean guide](../README.md#clean-the-duplicates)):
> otherwise both copies of a photo are sorted, and one of them gets renamed.

## Run it

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene classify
```

After an audit with [the cache](../start/02-keep-the-cache.md), nothing is read again: the dates,
the cameras and the places come from the cache, and the audit's fingerprints tell the duplicates
still there. The reports folder receives the workbook where you correct the proposal
([step 5](05-review-the-proposal.md)).

<!-- capture: classify.txt -->
```text
─────────────────────────────────── Classify ───────────────────────────────────
Already in place: 43 of 80 (54%).
Proposal
┏━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┓
┃ Band    ┃ Files ┃ To move ┃
┡━━━━━━━━━╇━━━━━━━╇━━━━━━━━━┩
│ Sure    │    74 │      31 │
│ To sort │     3 │       3 │
│ Undated │     3 │       3 │
└─────────┴───────┴─────────┘

Why
┌────────────────────┬────┐
│ Existing folders   │ 74 │
│ no-signal          │  3 │
│ undated            │  3 │
│   Seaside holidays │ 13 │
│   Photos 2019      │ 12 │
│   Mountain hike    │ 10 │
│   Birthday         │  8 │
│   Old phone        │  8 │
│   Christmas        │  6 │
│   Lake             │  6 │
│   Phone            │  6 │
│   Christmas 2020   │  4 │
│   WhatsApp         │  1 │
└────────────────────┴────┘

⚠️  Rules that decided nothing: Films and series, Screenshots and documents,
Event neighbours, Christmas, New Year.
💡 Check their dates, their patterns and their order in config.toml.
To check or to sort: 3 files in 1 event.
💡 32 exact duplicates are still there: run 'clean' first, otherwise both copies
are sorted.
💡 Nothing was changed: 'classify' only proposes.
✅ Workbook to edit: /reports/20261001-121157-classify/classify.xlsx
✅ Report with the photos: /reports/20261001-121157-classify/report.html
💡 Edit the yellow cells and save: nothing moves until 'sort'.
```

## Read the result

*Already in place* counts the files that already sit where the proposal wants them. After a few
sorts, it is how far your collection is.

*Proposal* gives the files of each band, and how many of them would move:

- **Sure**: a folder name you chose (`2019/Seaside holidays` stays `2019/Seaside holidays`), or a
  reliable date when the layout needs no category. They go to `year/category`.
- **To check**: a guess the tool is not sure of, for instance a photo whose date contradicts its
  folder. They are gathered in `year/To check/category`: look at them in the report, and confirm
  them in the workbook ([step 5](05-review-the-proposal.md)).
- **To sort**: nothing tells where they belong. They are gathered in `year/To sort/<event>`, one
  folder per event (photos taken close together, across folders and phones), so that you name
  an event once: in the workbook, name the event `2016-07-14` `Kermesse`, and its files go to
  `2016/Kermesse`.
- **Undated**: only the file's date on the disk is known, which says when it was copied, not
  when it was taken. They go to `To sort/Undated`, or to `To sort/Received and downloaded` when
  no camera took them (pictures received in a messaging app).
- **Left as they are**: your protected folders and the folders you asked to leave alone.

*Why* gives the rule (or the reason) of each proposal, then the categories found most.

## Where the dates come from

The first reliable source wins: the date the camera wrote (EXIF), the tags of a video (its UTC
time brought back to your local time: a New Year's Eve video stays in its year), the file name
(`IMG_20210712_…`, WhatsApp names), the folder (`2016`, `Juillet 2016`), and last the date on
the disk. A camera whose clock was never set is spotted: its folders' dates win.

An event keeps the year of its start, and a folder you named keeps the year of its oldest
photo: a party on New Year's Eve is not cut in two.

## Your own structure

Everything is in the `[classify]` section of `config.toml` ([step 7](../clean/07-configuration-file.md)),
and every value there is an example to replace:

- `--layout "{year}/{month}"`: sort by month, with no category at all.
- `--target 'D:\Photos sorted'`: build the tree elsewhere (the folder must be mounted); by
  default each mounted folder is reorganised in place.
- `--year 2016`, or `--year 2015-2017`: one year at a time, one evening at a time.
- `--leave 'C:\Photos\Albums'`: a folder never sorted, still analysed and cleaned.

Layouts accept `{year}`, `{quarter}`, `{month}`, `{month_name}`, `{day}`, `{category}`,
`{event}` and `{event_start}`. An empty layout leaves the files where they are.

The categories come from rules you order and complete: your folders, your trips, your
birthdays, Christmas, screenshots ([step 6](06-write-down-what-you-know.md)).

---

← [3. Several folders and disks](../start/03-several-folders.md) · [Documentation](../README.md) · Next: **[5. Review the proposal](05-review-the-proposal.md)** →
