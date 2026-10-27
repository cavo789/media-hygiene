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
out: they are never changed.

## Step 1: tick them

```powershell
mh review --intruders
```

The page lists the intruder files twice, **per extension** and **per folder**, with how many
files and how much room each one takes. Tick extensions, folders, or both, then **Set the files
ticked aside**:

- an extension alone: every file of that type, wherever it lies;
- a folder alone: every intruder file of that folder and its subfolders;
- both: the files of a ticked extension lying in a ticked folder.

**Nothing moves here.** A docx may matter: nothing is set aside without you. Each pick is saved
at once in `decisions.json` of the reports folder; the list under the tables is that file, read
back from the disk. **Put every intruder file back** empties it again.

## Step 2: apply

Stop the page with Ctrl+C, then run `clean` with the decisions file:

```powershell
mh clean --decisions decisions.json
```

The files set aside go to the quarantine of their drive, journaled: `undo` brings them back. A
file changed or moved since you ticked it is left where it is.

---

← [14. Unwanted photos](14-unwanted-photos.md) · [Documentation](../README.md)
