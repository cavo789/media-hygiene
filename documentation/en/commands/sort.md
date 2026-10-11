# `sort`: move the files as the workbook says

[Documentation](../README.md) › [Commands](../reference-commands.md) › `sort` · 🇫🇷 [Français](../../fr/commands/sort.md)

`sort` applies the workbook of [`classify`](classify.md), with your edits: it checks it, says
what it will do, **asks**, then moves each file to its folder. On one disk, a move is a rename:
nothing is copied, no space is used. Every move is journaled, `undo` puts everything back, and
the end proves that nothing was lost.

## At a glance

| | |
|---|---|
| Your photos | ✋ Acts: moves the photos and videos, removes the source folders it leaves empty. Never over another file, never deletes a photo. |
| Needs | Your folders **without** `:ro`, `/journal`, and `/reports` (the `classify` run). |
| Recommended | `/quarantine` (for the `Thumbs.db` and the like of the folders left empty), `/cache` (it follows the moves). |
| Writes | The journal, the moves, the proof in `/reports/<run>-sort/manifest.json`. |
| Undo | [`undo`](undo.md): the files go back, the removed folders come back. |
| With `mh` | `mh sort`. |

## When to use it

Once you have reviewed the proposal ([sorting, step 5](../sort/05-review-the-proposal.md)) and,
if you wish, named the events in the browser ([`review-sort`](review-sort.md)). **Save and close
the workbook first.**

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

## Good to know

- **Companions travel together**: a Live Photo (`IMG_1.HEIC` + `IMG_1.MOV`), a RAW file and its
  JPEG, and their sidecars go to the same folder.
- **Across disks** (two `-v` are two disks), a file is copied, compared, and only then removed.
- **An existing file is never overwritten**: `IMG_1.jpg` becomes `IMG_1 (2).jpg`.
- **Stopped in the middle?** Run the same command again: the files already moved count as done.
  `undo` then undoes all the runs of that workbook at once.
- **Nothing lost, proven**: the files and sizes of the source and target folders are counted
  before and after, and must match.

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
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
