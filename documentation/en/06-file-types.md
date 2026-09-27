# 6. Only some file types

[Documentation](README.md) › Step 6 of 13 · 🇫🇷 [Français](../fr/06-file-types.md)

By default, the tool analyses every photo, RAW file and video, and nothing else. `--ext` narrows
the analysis to some types, or widens it to other files.

## What is analysed by default

Files are recognised by their extension, whatever its case:

| Type | Extensions |
|---|---|
| Images | avif, bmp, gif, heic, heif, jpe, jpeg, jpg, png, tif, tiff, webp |
| RAW (decoded by LibRaw, previewed from the JPEG the camera embeds) | arw, cr2, cr3, dng, nef, orf, pef, raf, rw2, srw |
| Videos | 3g2, 3gp, avi, flv, m2ts, m4v, mkv, mov, mp4, mpeg, mpg, mts, ts, webm, wmv |

`media-dedup audit --help` lists them too. [Sidecars](reference-sidecars.md) (`.xmp`, `.aae`,
`.thm`) are not analysed on their own: they follow their photo.

## Only some types

`--ext` takes one or more extensions, comma-separated or repeated (`--ext heic --ext mp4`); case
and leading dot do not matter. For instance, only the iPhone photos and the videos:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Old disk:/data/d/Old disk:ro" `
  -v media-dedup-cache:/cache `
  cavo789/media-dedup audit --ext heic,mp4
```

The audit starts by saying what it analyses:

<!-- capture: audit-ext.txt|Only these|└ -->
```text
⚠️  Only these extensions are analysed: .heic, .mp4.

Audit summary
┌────────────────────────────────────┬────────┐
│ Media files scanned                │      9 │
│ Groups of identical files          │      4 │
│ Extra copies that can be deleted   │      4 │
│ Space that can be freed            │ 5.9 MB │
│ Broken files (empty or unreadable) │      1 │
│ Duration                           │    0 s │
└────────────────────────────────────┴────────┘
```

## Other file types

The tool is made for photos and videos, but `--ext` also accepts other extensions, for instance
to find the duplicate documents of a family folder. `clean` ([step 8](08-clean.md)) then needs
the `/quarantine` mount:

```powershell
docker run --rm -it `
  -v "C:\Users\Me\Documents:/data/c/Users/Me/Documents" `
  -v "$HOME\media-dedup\journal:/journal" `
  -v "$HOME\media-dedup\quarantine:/quarantine" `
  cavo789/media-dedup clean --ext pdf,docx
```

Such files are handled with more care than photos. For a photo, the folder is only a way to
sort; for a document or a program, **where the file lies can be what makes it work**: an
identical `LICENSE`, `__init__.py` or template in two projects is expected, and deleting "the
copy" breaks one of them.

- **Only compared**, byte for byte: never decoded (images go through Pillow, RAW files through
  LibRaw, videos through `ffprobe`; other types have no check), no preview, no near duplicates.
  An empty file is never "broken": it may be a marker a program needs.
- **Their copies are moved to the quarantine**, never deleted: `clean` refuses to run without
  the `/quarantine` mount. `undo` puts them back; `purge` deletes them for good.
- **Software folders are skipped**: `.git`, `.hg`, `.svn`, `node_modules`, `.venv`, `venv`,
  `site-packages`, `__pycache__`, `AppData`, `ProgramData`, `Program Files`,
  `Program Files (x86)` and `Windows`, whatever their case.
- **A typo is not refused**: `--ext jpgg` is a valid extension that simply matches nothing. The
  audit names the extensions that are not photos or videos: read that warning.
- **`--ext` still limits the analysis**: `--ext jpg,pdf` analyses JPEG photos and PDF documents,
  not the RAW files and videos.

Mount the folders holding your documents, never a whole drive or `C:\Users`: programs and their
data live there too.

---

← [5. Choose which copy stays](05-choose-the-kept-copy.md) · [Documentation](README.md) · Next: **[7. The configuration file](07-configuration-file.md)** →
