# `review-sort`: name the events in your browser

[Documentation](../README.md) › [Commands](../reference-commands.md) › `review-sort` · 🇫🇷 [Français](../../fr/commands/review-sort.md)

## In short

**Give a name to each outing, party or trip of your photos while looking at them: that name
becomes their folder when [`sort`](sort.md) tidies your collection.**

`review-sort` shows **one [event](../reference-glossary.md#event) at a time** in your browser,
with its photos, the proposal of [`classify`](classify.md) and a field to name it, with the
keyboard. Nothing moves here: your choices are saved next to the proposal, and `sort` is what
moves the files.

**When**: optional, between `classify` and `sort`. The Events sheet of the
[workbook](../reference-glossary.md#workbook) does the same work, without the photos in front of
you; both can be used together.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene review-sort
```

## What it is for

**An event is a moment of your life seen through your photos**: a school fair, a weekend at the
seaside, a Christmas. `classify` finds them on its own: photos and videos taken without a break of
more than 6 hours (a night does not cut a weekend in two), at least 5 files, **from one folder or
phone to another**. The photos of the fair taken with your phone, Julie's and the camera make one
event, even when they sit in three folders.

What `classify` does not know is **what to call it**. Without a hint (a folder you had already
named, a [rule](../sort/06-write-down-what-you-know.md)), it can only file it under its dates, in
`2016/To sort/2016-07-14`. Name it `Kermesse`, and `sort` puts all its files **in one folder**,
`2016/Kermesse`:

```text
Before, three folders:
  C:\Photos\DCIM\100APPLE\IMG_4012.HEIC
  C:\Photos\Julie's phone\20160714_153201.jpg
  C:\Photos\Import 2016\DSC_0815.JPG

After sort, one:
  C:\Photos\2016\Kermesse\IMG_4012.HEIC
  C:\Photos\2016\Kermesse\20160714_153201.jpg
  C:\Photos\2016\Kermesse\DSC_0815.JPG
```

So yes, it is a tree of folders on your disk: **each photo is moved into one folder only**, its
event's (on the same disk, a mere rename, and [`undo`](undo.md) puts everything back). For a photo
to show up elsewhere too ("every Christmas", "Grandma"), without a copy: the
[albums](../sort/12-albums.md).

- **One field, the folder.** Type the folder under the year: `Kermesse` gives `2016/Kermesse`,
  `Parties/Kermesse` gives `2016/Parties/Kermesse` (the fair and a birthday both under
  `Parties`). The line under the field says, as you type, where the files go: "→ 212 files go to
  C:\Photos\2016\Parties\Kermesse". The event's name (for the albums) is the last folder; change
  it under *Name of the event* if needed.
- **Not every event needs a name.** An event whose photos already sit in a named folder
  (`Seaside holidays`) has a proposal marked **sure**. Still look where it leads before accepting
  it: only its loose files (a phone's `DCIM`, files to check or to sort) go to the proposed folder.
- **Your own folders are never flattened.** An event that spans several folders you had named (a
  trip: `Montenegro/Budva`, `Montenegro/Cetinje`…) keeps them: accepted as proposed (with
  <kbd>Enter</kbd> or <kbd>V</kbd>), each file stays in its folder; given another folder
  (`Holidays in Montenegro`), that folder becomes their parent: `2019/Holidays in
  Montenegro/Budva`, `2019/Holidays in Montenegro/Cetinje`. The page says it: "3 files keep their
  own folder (Budva, Cetinje)".
- **An event you do not name** is not lost: it goes to `year/To sort/<its dates>`, where you find
  it again.

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed, nor the workbook: mount the photos `:ro`. |
| Needs | `/reports` (the `classify` run), your folders (to show the photos), and `-p 127.0.0.1:8088:8088`. |
| Writes | `sort-decisions.json`, next to `plan.json` in the folder of the `classify` run. |
| Undo | `Delete` in the page takes a choice back; the workbook then decides again. |
| With `mh` | `mh review-sort`: the port is published for you. |

## Run it

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene review-sort
```

It counts the events (*412 events to decide: 260 with a sure proposal (one click), 152 to look
at*), then prints the address of the page: Ctrl+click it. Ctrl+C, or closing its tab, stops it; the next run resumes.

## The main keys

The page: the event shown on the left (its dates, its folders, the proposal, what the workbook
says), its folder and where its files go in the bar on top, its photos under them. The keys stay at the
bottom left, under ⌨ **Keyboard** (the first ones always shown, the others under *More keys*),
with the line saying where each choice is saved.

| Key | What it does |
|---|---|
| `Enter` | Save the folder, then go to the next event still to decide. |
| `N` / `P` | Next or previous event, without deciding. `U`: next event still to decide. |
| `V` | Accept every sure proposal at once; `Shift`+`Z` takes that batch back. |
| `F` / `E` | Type the folder / change the event's name; `Esc` drops what is typed and not saved. |
| `Shift`+`S` | Leave the whole event where it is. |
| `Space`, `O`, `S` | Select photos, send them to another category, or leave them where they are. |
| `Delete` | Take back the choice made here. |
| `Z` | Enlarge the photo. |

## Options

| Option | What it does |
|---|---|
| `WORKBOOK` | The `classify` workbook; the latest `classify` run's by default. |
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## Good to know

- **The workbook is never changed** (Excel may have it open). You may keep editing it: each
  choice of the page remembers what the workbook said when you made it.
- **A conflict is never settled silently**: if the workbook was changed since, on the same event
  or file, to something else, `sort` refuses and lists both values; the page shows them in red.
- **Run `classify` again**: your choices of the page are carried over to the yellow cells of the
  new workbook, like your edits.

## Go further

- [Sorting, step 11: name the events in your browser](../sort/11-name-events-in-the-browser.md)
- Next: [`sort`](sort.md).

## The built-in help

<details>
<summary><code>review-sort --help</code></summary>

<!-- capture: help-review-sort.txt -->
```text
 Usage: media-hygiene review-sort [OPTIONS] [workbook]

 🔒 Read-only: never changes your photos. Name the events of the classify
 proposal one by one in your browser.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   workbook      <str>  The classify workbook; the latest classify run's by   │
│                        default.                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --port          <int range> [x>=1]  Port of the page. docker run publishes   │
│                                     it under the same number on your         │
│                                     computer: -p 127.0.0.1:9000:9000 for     │
│                                     --port 9000. Default:  port in           │
│                                     config.toml, 8088.                       │
│ --help  -h                          Show this message and exit.              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
