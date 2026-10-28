# 4. Propose a tidy tree: `classify`

[Documentation](../README.md) › Sorting, step 4 · 🇫🇷 [Français](../../fr/sort/04-classify.md)

Steps 1 to 3 showed what your folders hold. `classify` goes one step further: for every photo and
video, it proposes a place in a tidy tree. It **only proposes**: nothing moves, and folders
mounted `:ro` are fine.

## The convention: year, month, event

Every file you sort goes to `year/year-month/event`, a tree that reads in Explorer **without
media-hygiene**, the day the tool is gone:

```text
2009\
  2009-11\
    Anniversaire de Tom\      ← an event you named
    IMG_4410.jpg              ← looked at: nothing special that month
  2009-12\
    Saint Nicolas 2009\
2019\
  2019-07\
    Montenegro\
      Budva\                  ← a stage of a trip, one level below it
1985\
  1985-00\                    ← only the year is known (a scan)
```

`2009-11`, not `11`: a month folder copied alone, or seen in Explorer's search results, still
says its year. The month is that of the event's **start**, `00` when only the year is known.
The tool writes **no word of its own** in the tree: only digits and the names you typed.
**A file moves once, to its real place**: what is not decided stays where it is until you decide
(in [`review-sort`](../commands/search.md#the-events-of-the-latest-classify) or [`search`](../commands/search.md)).

> 💡 A `config.toml` written by an older version sorts otherwise (`{year}/{category}`, *To check*
> and *To sort* folders): `classify` says so in one line, and `mh config --convention` shows the
> change and asks before writing it.

> 💡 Clean the duplicates first ([the clean guide](../README.md#clean-the-duplicates)):
> otherwise both copies of a photo are sorted, and one of them gets renamed.

## Run it

```powershell
mh classify
```

<details>
<summary>Without <code>mh</code>: the full command</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene classify
```

</details>

After an audit with [the cache](../start/02-keep-the-cache.md), nothing is read again: the dates,
the cameras and the places come from the cache, and the audit's fingerprints tell the duplicates
still there. The reports folder receives the workbook where you correct the proposal
([step 5](05-review-the-proposal.md)).

<!-- capture: classify.txt -->
```text
🔒 Read-only: your photos and videos are not touched.
─────────────────────────────────── Classify ───────────────────────────────────
24 unchanged folders taken from the index, 0 read.
💡 A photo changed in place by another program? 'audit --full' reads every
folder (done anyway for those listed 7 days ago).

Already in place: 43 of 86 (50%).
Proposal
┏━━━━━━━━━┳━━━━━━━┳━━━━━━━━━┓
┃ Band    ┃ Files ┃ To move ┃
┡━━━━━━━━━╇━━━━━━━╇━━━━━━━━━┩
│ Sure    │    77 │      34 │
│ To sort │     5 │       5 │
│ Undated │     4 │       4 │
└─────────┴───────┴─────────┘

Why
┌───────────────────────────┬────┐
│ Existing folders          │ 76 │
│ No signal                 │  5 │
│ Undated                   │  4 │
│ Screenshots and documents │  1 │
└───────────────────────────┴────┘

Largest categories
┌──────────────────┬────┐
│ Seaside holidays │ 13 │
│ Photos 2019      │ 12 │
│ Mountain hike    │ 10 │
│ Birthday         │  8 │
│ Old phone        │  8 │
│ Christmas        │  6 │
│ Lake             │  6 │
│ Phone            │  6 │
│ Christmas 2020   │  4 │
│ WhatsApp         │  3 │
└──────────────────┴────┘

⚠️  Rules that decided nothing: Films and series, Event neighbours, Christmas,
New Year.
💡 Check their dates, their patterns and their order in config.toml.
To check or to sort: 5 files in 1 event.
💡 Nothing was changed: 'classify' only proposes.
✅ Workbook to edit:
C:\Users\you\media-hygiene\reports\20261025-084657-classify\classify.xlsx
✅ Report with the photos:
C:\Users\you\media-hygiene\reports\20261025-084657-classify\report.html
👉 What next: edit the yellow cells and save; nothing moves until 'sort'.
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "D:\Old disk:/data/d/Old disk" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "media-hygiene-cache:/cache" `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene sort
💡 32 exact duplicates are still there: run 'clean' first, otherwise both copies
are sorted.
```

## Read the result

*Already in place* counts the files that already sit where the proposal wants them. After a few
sorts, it is how far your collection is.

*Proposal* gives the files of each band, and how many of them would move:

- **Sure**: a folder name you chose (`2019/Seaside holidays` becomes
  `2019/2019-08/Seaside holidays`), or a rule of yours. They go to `year/year-month/event`.
- **To check**: a guess the tool is not sure of, for instance the loose photos of an event whose
  other photos lie in a folder you named. They **stay where they are**; the review page shows
  where they would go, and confirming them moves them there ([step 5](05-review-the-proposal.md)).
- **To sort**: nothing tells where they belong. They stay where they are, grouped by event
  (photos taken close together, across folders and phones), so that you name an event once: name
  the event `2016-07-14` `Kermesse`, and its files go to `2016/2016-07/Kermesse`.
- **Undated**: only the file's date on the disk is known, which says when it was copied, not
  when it was taken. They stay where they are.
- **Left as they are**: your protected folders, the folders you asked to leave alone, and the
  files you put directly in their `year/year-month` folder (nothing special that month).

| What the tool knows | Where the file goes |
|---|---|
| decided (a folder you named, a rule, your choice on a page) | `year/year-month/event` |
| a guess, nothing, no date | stays where it is until you decide |
| a received picture (WhatsApp…) | a guess: the event of the day it was received, to confirm |
| a screenshot, a ticket | stays, or the folder of a `kind` rule of yours |

> 💡 Many received pictures are smaller copies of photos you hold as originals: run
> [`clean --tier near`](../clean/11-near-duplicates.md) first.

*Why* gives the rule (or the reason) of each proposal, then the categories found most.

**A photo kept in a generic folder after a clean.** When [`clean`](../clean/08-clean.md) removed
a copy, the photo kept remembers the copy's folder. A photo whose own folders say nothing
(`DCIM`, `Camera`) reads that folder as if it lay there: its copy in `Mariage Julie 2015` makes
it `Mariage Julie 2015`, a copy in `2017/Durbuy` names the town. Its own folders always come
first. Two removed copies in folders that disagree (`Mariage Julie`, `Noël`): neither is used,
and the photo waits for you where it is. The workbook's *why* says where the hint came from:
`(the folder of a removed copy: D:\Backup\Mariage Julie 2015)`.

**Your family's photos of a trip you sorted.** The photos of a person's folder (`2019/Photos
Chloé`) taken while your own folders of the event hold photos join them, to check: the
`same_moment` rule ([step 6](06-write-down-what-you-know.md#your-familys-folders)).

## Where the dates come from

The first reliable source wins: the date the camera wrote (EXIF), the tags of a video (its UTC
time brought back to your local time: a New Year's Eve video stays in its year), the file name
(`IMG_20210712_…`, WhatsApp names), the folder (`2016`, `Juillet 2016`), and last the date on
the disk. A camera whose clock was never set is spotted: its folders' dates win.

An event keeps the year of its start, and a folder you named keeps the year of its oldest
photo: a party on New Year's Eve is not cut in two.

## Your own structure

Everything is in the `[classify]` section of `config.toml` ([cleaning, step 7](../clean/07-configuration-file.md)),
and every value there is an example to replace:

- `--layout "{year}/{month}"`: sort by month, with no category at all.
- `--target 'D:\Photos sorted'`: build the tree elsewhere (the folder must be mounted); by
  default each mounted folder is reorganised in place.
- `--year 2016`, or `--year 2015-2017`: one year at a time, one evening at a time. The files
  only the disk dates wait for a run without `--year`.
- `--leave 'C:\Photos\Albums'`: a folder never sorted, still analysed and cleaned.

Layouts accept `{year}`, `{year_month}`, `{quarter}`, `{month}`, `{month_name}`, `{day}`,
`{category}`, `{event}` and `{event_start}`. An empty layout leaves the files where they are.
Year and month come from the same date: **the start of the event**. A trip from 28 August to
5 September goes whole to `2009/2009-08`, a New Year's Eve party to `2009/2009-12`; a folder you
named takes the month of its oldest file. When only the year is known (a folder `1985`, a scan),
the month is **`00`**: `1985/1985-00`, a digit that reads the same in every language and sorts
before January. `event_year = "per_file"` dates each file on its own instead.

The categories come from rules you order and complete: your folders, your trips, your
birthdays, Christmas, screenshots ([step 6](06-write-down-what-you-know.md)).

---

← [3. Several folders and disks](../start/03-several-folders.md) · [Documentation](../README.md) · Next: **[5. Review the proposal](05-review-the-proposal.md)** →
