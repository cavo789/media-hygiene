# Sort in short: the whole path

[Documentation](../README.md) › Sort in short · 🇫🇷 [Français](../../fr/sort/quick-guide.md)

Every command of the sort, in order, ready to paste into **PowerShell**. Each step links to its
detailed page, should you want to understand. Replace `C:\Photos` with your folder.

The principle: `classify` **proposes** a place for each photo and video (`year/category` by
default), you correct the proposal in a workbook, and only `sort` moves the files. Nothing moves
before, and `sort` can be undone.

## 0. Before you start

**Clean the duplicates first** ([clean in short](../clean/quick-guide.md)): otherwise both copies
of a photo are sorted. The `mh` command written for the clean serves here too; otherwise, write it
once: [clean in short, step 0](../clean/quick-guide.md#0-once-write-the-mh-command). In a new
terminal, load it again:

```powershell
. "$HOME\media-hygiene\mh.ps1"
```

## 1. Ask for a proposal

```powershell
mh classify
```

Nothing is modified: `mh` mounts your folders read-only (`:ro`). At the end, two files in a new
`<date>-classify` folder of your reports:

- `classify.xlsx`, the workbook, to open in Excel or LibreOffice: that is where you **edit**;
- `report.html`, the report, to open in your browser: that is where you **look** at the photos.

Details: [propose a tidy tree](04-classify.md).

## 2. Correct the proposal

Open both side by side. Only the **yellow** cells of the workbook can be edited.

1. **Start with the Events sheet**: the largest first. Type a **Name** (`Italy 2023`): it becomes
   the folder of the event. Naming the first ten rows often settles most of the collection.
2. To understand an event, look for its identifier in the report: its dates, its previews, where
   its photos come from.
3. A file in the wrong place? Files sheet, **Final folder** column (`2016/Kermesse`).
4. **Save and close** the workbook.

Rather in the browser, one photo on screen? [Name the events in the
browser](10-name-events-in-the-browser.md) does the same with the keyboard. Details: [review the
proposal](05-review-the-proposal.md).

## 3. Write down what you know (optional)

Your trips, your parties, your existing folders: written once as rules in
`$HOME\media-hygiene\config\config.toml`, they serve every `classify`. For instance:

```toml
[[classify.rules]]
name = "Italy 2023"
match = "date_range"
dates = "2023-07-01..2023-07-15"
category = "Holidays and outings/Italy 2023"
```

Then run step 1 again: the edits already made in the old workbook are carried over to the new
one. Details: [write down what you know](06-write-down-what-you-know.md).

## 4. Sort

```powershell
mh sort
```

For `sort`, `mh` mounts your folders writable (`sort` moves files) and adds the journal and the
quarantine. `sort` takes the workbook of the last `classify`, checks it, says how many edits it read (too
few? the workbook was not saved) and asks for confirmation: answer `y`. It ends by proving that
nothing is lost: as many files, of the same size, before and after. Details: [sort](07-sort.md).

## 5. Check, or undo

```powershell
explorer "C:\Photos"
```

You change your mind? `mh undo`: each file goes back where it was.

## Going further (optional)

- [Places and trips from the GPS](09-places-from-gps.md): name your places on a map, and let the GPS
  sort home, family and trips.
- [Name subjects with a local model](08-subjects-from-a-local-model.md): what the lone photos
  show, without sending anything to the Internet.
- [Albums](11-albums.md): one photo in several folders, with no copy and no space taken.

<details>
<summary>Without <code>mh</code>: the full commands</summary>

Step 1, read-only:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene classify
```

Steps 4 and 5: `:ro` is gone, `/journal` and `/quarantine` are added; `undo` instead of `sort` to
undo:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  cavo789/media-hygiene sort
```

</details>

---

[Documentation](../README.md) · Step by step: **[4. Propose a tidy tree](04-classify.md)** →
