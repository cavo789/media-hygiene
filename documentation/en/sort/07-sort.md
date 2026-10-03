# 7. Sort: apply the workbook

[Documentation](../README.md) › Sorting, step 7 · 🇫🇷 [Français](../../fr/sort/07-sort.md)

You reviewed the proposal and edited the workbook ([step 5](05-review-the-proposal.md)). `sort`
now moves the files where the workbook puts them. Like `clean`, every move is journaled and
`undo` puts everything back.

## Run it

Save and close the workbook first. Then mount your folders **without** `:ro`, with the journal,
the quarantine and the reports folder of `classify`:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\reports:/reports" `
  cavo789/media-hygiene sort
```

Without an argument, `sort` takes the workbook of the latest `classify` run. To apply another one,
give its path: `sort "C:\Users\me\Desktop\classify.xlsx"` (in a mounted folder). A copy edited
elsewhere is fine: its `plan.json` is found in `/reports` by the id the workbook holds.

Before anything moves, `sort` says what it read and what it will do, then asks:

<!-- capture: sort.txt|re:^─+ Sort|❓ -->
```text
───────────────────────────────────── Sort ─────────────────────────────────────
Workbook: /reports/20261003-080751-classify/classify.xlsx
0 edits read; workbook saved on 3 October 2026 at 08:07.
Sort
┌──────────────────────────────┬────────┐
│ Files to move                │      4 │
│ Into folders                 │      2 │
│ Size                         │ 5.9 MB │
│ Already in place             │     40 │
│ Staying where they are       │      0 │
│ Going to a 'to check' folder │      0 │
│ Going to a 'to sort' folder  │      1 │
│ Source folders removed       │      2 │
└──────────────────────────────┴────────┘
🛟 Each file is moved, never over another one nor deleted; the run is journaled:
'undo' puts everything back.
❓ Move 4 files into 2 folders? [y/N] y
```

- *edits read* counts the cells you filled; check the date: a workbook edited but **not saved**
  shows its old date, and `sort` warns when Excel or LibreOffice still has it open.
- The choices made in [the browser page](10-name-events-in-the-browser.md#where-your-choices-go),
  if any, are applied on top of the workbook, and counted on a line of their own.
- *Already in place*: files counted, not moved.
- *Source folders removed*: the folders the sort leaves empty (see below).

Add `--yes` to skip the question, or set `confirm = false` in the `[sort]` section of
`config.toml`.

## What is checked first

The whole workbook is compared with its `plan.json`, **all or nothing**: the sheet names and
their order, the header rows, the rows (each id exactly once) and every locked cell. The first
difference refuses the whole file, naming the cell, the value expected and the value found:

```text
❌ Files!J2: expected '2016/To sort/2016-07-14', found 'Elsewhere'.
💡 Undo the change in Excel (Ctrl+Z), restore a copy of the workbook, or run
'classify' again: your edits are carried over to its new workbook.
```

Then the yellow cells: a name Windows refuses (`CON`, `a:b`, a trailing dot), a folder that
climbs out of the target (`..`) or a path longer than Windows accepts is refused with its cell.

The mounts are checked as for `clean`: a journal is required, and read-only folders are refused.
The target must be a mounted folder (a folder of the container itself would vanish with it) and
must not be inside a protected folder. Files of protected folders never move.

## How files move

- Each file is checked again just before it moves: a file changed or deleted since `classify` is
  skipped and listed. Files that are not in the plan are never touched.
- On the same disk, a file is renamed: instant. Across disks (two `-v` options are two disks, even
  on the same drive), it is copied, compared with the original, and only then removed.
- An existing file is never overwritten: `IMG_1.jpg` becomes `IMG_1 (2).jpg`.
- **Companions travel together**: a Live Photo (`IMG_1.HEIC` + `IMG_1.MOV`), a RAW file and its
  JPEG, and their [sidecars](../reference-sidecars.md) go to the same folder, with the same name.
  Their folder is the final folder typed on any of their rows of the Files sheet; else an event
  or category edit reaching one of them (the photo's first, then the RAW file's, then the
  video's: `sort` says "IMG_1.MOV follows IMG_1.HEIC" when their edits gave different folders);
  else the photo's proposal. Two different final folders typed for the same companions (or a
  folder and *(stay where it is)*) make `sort` refuse the workbook before moving anything, naming
  both cells: give them the same folder, or clear all but one.
- The cache follows: the next `audit` does not read the moved files again.

## Folders left empty

A source folder left empty is removed, the deepest first, so that sorting in place does not leave
hundreds of empty `July 2016` folders behind. A folder holding only `Thumbs.db`, `desktop.ini` or
`.DS_Store` counts as empty: those files go to the quarantine first (the list is `junk_files` in
`[sort]`). A folder holding anything else stays, and `sort` says how many stay and why. Your
mounted folders, protected and excluded folders are never removed. `--keep-empty-folders` keeps
them all.

## Nothing lost, proven

The files of the source folders and of the target are counted before the moves and again after:
the counts and the sizes must be equal. Every move is checked (file at its target, same size, same
SHA-256 when it crossed disks):

<!-- capture: sort.txt|re:^Sort \d| -->
```text
Sort 20261003-080753
┌──────────────────────────┬────────┐
│ Files processed          │      4 │
│ Size                     │ 5.9 MB │
│ Skipped (left untouched) │      0 │
│ Failed                   │      0 │
│ Duration                 │    0 s │
└──────────────────────────┴────────┘
Source folders removed: 2.
✅ Nothing lost: 46 files (17.6 MB) before and after; 4 of 4 moves verified.
Manifest: /reports/20261003-080753-sort/manifest.json
💡 Changed your mind? 'media-hygiene undo 20261003-080753' moves everything
back.
```

The proof is written to `/reports/<run>-sort/manifest.json`.

## Classify again after a sort

Run `classify` again after a sort (new photos, a rule changed): the files already sorted are in
place and are not proposed elsewhere. The **"to check" files you did not confirm** stay in their
`<year>/To check/<category>` folder, still to check, with the reason `previous-guess`: their
folder is the tool's own guess, so a new run does not guess again and `sort` does not move them
back and forth. They leave it when you decide: confirm or rename the category, or give the file
or its event a folder, in the new workbook. A rule of [step 6](06-write-down-what-you-know.md)
that is sure of them (a date range, a path, a camera) moves them too.

The same goes for the **"to sort" files** of an event the tool named after a folder
(`2019/To sort/Seaside holidays`): that name is the tool's own, not a folder you chose, so the
files stay there, still to sort. Give the event a name in the workbook to move them.

## Stopped in the middle

70,000 moves take a while, and a laptop sleeps. Ctrl+C finishes the current file, closes the
journal and says what was done. Run the same command again: the files already moved by this
workbook are counted as done, and the sort goes on.

## Change your mind

A sort run is undone like a clean run ([undo](../clean/09-undo-history-purge.md)): the files go
back, the removed folders come back, the folders the sort created go.

<!-- capture: undo-sort.txt -->
```text
────────────────────── Undo the sort run 20261003-080753 ───────────────────────
🛟 Each file comes back where it was, never over another one; what cannot come
back whole is left as it is, and said.

Undo the sort run 20261003-080753
┌──────────────────────────┬────────┐
│ Files processed          │      4 │
│ Size                     │ 5.9 MB │
│ Skipped (left untouched) │      0 │
│ Failed                   │      0 │
│ Duration                 │    0 s │
└──────────────────────────┴────────┘
```

A sort resumed after an interruption is several runs of the same workbook, and one operation:
`undo` of any of them undoes them all, newest first, even when you name an earlier one (no later
move stays on top). It lists them first (run, start, files moved) and asks once; `--yes` skips
the question, as for `sort`. A run already undone on its own is left aside, and said so. `history`
lists the runs.

---

← [6. Write down what you know](06-write-down-what-you-know.md) · [Documentation](../README.md) · Next: **[8. Name the subjects with a local model](08-subjects-from-a-local-model.md)** →
