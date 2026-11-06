# 15. Intruder files

[Documentation](../README.md) › Cleaning, step 15 of 15 · 🇫🇷 [Français](../../fr/clean/15-intruder-files.md)

A zip, a Word document or a PDF copied among the family photos takes room and is never
compared. The audit counts them and says so at its end:

```text
🧹 3 files that are not photos or videos (zip, pdf) take 12 MB in your photo folders: see
'Intruder files' in the report; 'review --intruders' picks those to set aside.
```

Companions are never intruders: sidecars (`.xmp`, `.aae`), Takeout `.json`, `Thumbs.db`,
`desktop.ini`… (`[scan] companions` in `config.toml`). Protected and backup folders are left
out: they are never changed. A `.mpo` (the 3D or multi-picture JPEG of some cameras) is a
photo, not an intruder.

Three ways lead to the page: the command below, the report's *Intruder files* section (its
command to copy, or its button when the home page serves the report), and the **Intruder
files** tile of *Where you are* on the home page, which shows their weight at the last audit:
a click opens the page (with none, it opens the Clean space).

From the home page, the page has *Back to the home page* and its sidebar. Typed in the console,
there is no home page behind it: its top bar says so (`Ctrl+C` in the console ends the page, then
`mh` opens the home page) and no sidebar entry is drawn.

## Step 1: tick them

```powershell
mh review --intruders
```

The page lists the intruder files twice, **per extension** and **per folder**, with how many
files and how much room each one takes. Tick extensions, folders, or both. The bar at the top
of the page, always in view, says in one sentence which files the ticks take, with their count
and size, and its red button carries that count (**Set these 12 files aside**):

- an extension alone: every file of that type, wherever it lies;
- a folder alone: every intruder file of that folder and its subfolders;
- both: the files of a ticked extension lying in a ticked folder.

While an extension is ticked, the folder table lists only the folders that hold some, each with
the count and size of that extension: you see where they are. A folder ticked works the same way
on the extension table. Untick everything to see every row again.

Many types, only a few to keep? Above the extension table, switch from **Set these aside** to
**Set everything aside but these** and tick the extensions to keep. The bar then names every
extension that will leave, with the count and size of its files, before you click.

Next to some extensions, a muted hint: *a cache, rebuilt by the device or the app* (`.ithmb`,
the thumbnails an iPod or iPhone sync writes: iTunes writes them again at the next sync), or
*keep it unless you have it elsewhere* (archives such as `.zip` or `.7z`, documents, audio,
image editors' projects). Any other extension gets none. It is a hint, never a verdict, and
never "delete": only you know whether a zip was extracted or a document is the only copy, and
what you pick goes to the quarantine, where `undo` finds it.

**Nothing moves here.** A docx may matter: nothing is set aside without you. Each pick is saved
at once in `decisions.json` of the reports folder; the list under the tables is that file, read
back from the disk. **Put every intruder file back** empties it again.

## Step 2: apply

Opened from the home page, the bar shows **Apply now** once something is set aside: `mh` runs
the step that moves them, with its usual question. Opened by its command, stop the page with
Ctrl+C, then run `clean` with the decisions file:

```powershell
mh clean --decisions decisions.json
```

The files set aside go to the quarantine of their drive, journaled: `undo` brings them back. A
file changed or moved since you ticked it is left where it is.

---

← [14. Unwanted photos](14-unwanted-photos.md) · [Documentation](../README.md)
