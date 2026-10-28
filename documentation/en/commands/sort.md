# `sort`: move the files as the workbook says

[Documentation](../README.md) › [Commands](../reference-commands.md) › `sort` · 🇫🇷 [Français](../../fr/commands/sort.md)

## In short

**Move your photos into the tidy tree you approved, with the proof that nothing was lost, and
undo it whenever you like.**

`sort` applies the [workbook](../reference-glossary.md#workbook) of [`classify`](classify.md), with your edits: it checks it, says
what it will do, **asks**, then moves each file to its folder. On one disk, a move is a rename:
nothing is copied, no space is used. Every move is journaled and `undo` puts everything back.

**When**: once you have reviewed the proposal ([sorting, step
5](../sort/05-review-the-proposal.md)) and, if you wish, named the events with
[`review-sort`](search.md#the-events-of-the-latest-classify). **Save and close the workbook first.**

**Try it**:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene sort
```

## At a glance

| | |
|---|---|
| Your photos | ✋ Acts: moves the photos and videos, removes the source folders it leaves empty. Never over another file, never deletes a photo. |
| Needs | Your folders **without** `:ro`, `/journal`, and `/reports` (the `classify` run). |
| Recommended | `/quarantine` (for the `Thumbs.db` and the like of the folders left empty), `/cache` (it follows the moves). |
| Writes | The journal, the moves, the proof in `/reports/<run>-sort/manifest.json`. |
| Undo | [`undo`](undo.md): the files go back, the removed folders come back. |
| With `mh` | `mh sort`. |

## Run it

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene sort
```

Before anything moves, it says what it read (the edits, the date the workbook was saved, the
choices of the browser page applied on top), what it will move, the files already in place and
the source folders it will remove, then asks.

## What is checked first

- **The whole workbook**, against its `plan.json`, all or nothing: sheets, headers, rows, every
  locked cell. The first difference refuses the file, naming the cell, the value expected and the
  value found.
- **The yellow cells**: a name Windows refuses, a folder that climbs out of the target (`..`) or
  a path too long is refused with its cell.
- **The mounts**, as for `clean`: a journal is required, read-only folders are refused; the
  target must be mounted and not inside a protected folder.
- **Each file, just before it moves**: one changed or deleted since `classify` is skipped and
  listed.

## Options

| Option | What it does |
|---|---|
| `WORKBOOK` | The edited workbook to apply (in a mounted folder); the latest `classify` run's by default. |
| `--yes`, `-y` | Do not ask (or `confirm = false` in `[sort]`). |
| `--keep-empty-folders` | Keep the source folders the sort leaves empty. |
| `--event ID` | Sort only the files of this event (its id: the first column of the Events sheet); the rest of the workbook is left for later. |

## Good to know

- **Companions travel together**: a Live Photo (`IMG_1.HEIC` + `IMG_1.MOV`), a RAW file and its
  JPEG, and their sidecars go to the same folder.
- **Across disks** (two `-v` are two disks), a file is copied, compared, and only then removed.
- **An existing file is never overwritten**: `IMG_1.jpg` becomes `IMG_1 (2).jpg`.
- **Stopped in the middle?** Run the same command again: the files already moved count as done.
  `undo` then undoes all the runs of that workbook at once.
- **Nothing lost, proven**: the files and sizes of the source and target folders are counted
  before and after, and must match.
- **One event at a time**: `--event` (or *Sort this event now* in
  [`review-sort`](search.md#the-events-of-the-latest-classify)) sorts one event; a later `sort` of the whole workbook skips
  its files, already moved. Each run has its own `undo`.
- **Everything stays linked**: right after moving, `sort` rewrites every file of yours that names
  photos by path — the names given to faces (`people\*.toml`), `albums.json`, `decisions.json`
  (burst series, files chosen in `search`; a folder pair whose folder is gone is dropped) and the
  videos chosen in `shrink --try` — then reads them back and says so in one line. They no longer
  depend on the cache: you can delete it. `undo` puts the old paths back the same way.
  A folder of `config.toml` (`[folders] preferred`, a folder placed on the map) that the run
  emptied is named, so that you can point it to the new folder.

## Go further

- [Sorting, step 7: sort](../sort/07-sort.md)
- [Sorting, step 5: the workbook](../sort/05-review-the-proposal.md#the-workbook-edit-the-yellow-cells)
- [Sort in short](../sort/quick-guide.md)

## The built-in help

<details>
<summary><code>sort --help</code></summary>

<!-- capture: help-sort.txt -->
```text
 Usage: media-hygiene sort [OPTIONS] [workbook]

 Move the photos and videos as the edited classify workbook says (journaled,
 undoable).

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   workbook      <str>  The classify workbook, edited; the latest classify    │
│                        run's by default.                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --yes                 -y        Do not ask for confirmation (overrides       │
│                                 sort.confirm).                               │
│ --keep-empty-folders            Keep the source folders the sort leaves      │
│                                 empty.                                       │
│ --help                -h        Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced: folders (override folders.* of config.toml) ──────────────────────╮
│ --backup        <str>  A backup or an old disk, mounted read-only: never     │
│                        changed, and not refused for being read-only (mh      │
│                        passes your backups). Repeatable.                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
