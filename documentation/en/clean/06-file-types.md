# 6. Only some file types

[Documentation](../README.md) › Cleaning, step 6 of 14 · 🇫🇷 [Français](../../fr/clean/06-file-types.md)

By default, the tool analyses every photo, RAW file and video, and nothing else. `--ext` narrows
the analysis to some types; the other files of your photo folders are listed by the audit.

## What is analysed by default

Files are recognised by their extension, whatever its case:

| Type | Extensions |
|---|---|
| Images | avif, bmp, gif, heic, heif, jpe, jpeg, jpg, png, tif, tiff, webp |
| RAW (decoded by LibRaw, previewed from the JPEG the camera embeds) | arw, cr2, cr3, dng, nef, orf, pef, raf, rw2, srw |
| Videos | 3g2, 3gp, avi, flv, m2ts, m4v, mkv, mov, mp4, mpeg, mpg, mts, ts, webm, wmv |

`media-hygiene config` lists them too, as the built-in categories `photo` (images), `raw`,
`video` and `media` (the three). [Sidecars](../reference-sidecars.md) (`.xmp`, `.aae`,
`.thm`) are not analysed on their own: they follow their photo.

## Only some types

`--ext` takes one or more categories or extensions, comma-separated or repeated (`--ext heic
--ext mp4`); case does not matter. A category names a whole list: `--ext video` analyses the
15 video extensions, `--ext photo,raw` every picture but no video. For instance, only the iPhone
photos and the videos:

```powershell
mh audit --ext heic,video
```

<details>
<summary>Without <code>mh</code>: the full command</summary>

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v "D:\Old disk:/data/d/Old disk:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene audit --ext heic,video
```

</details>

The audit starts by saying what it analyses:

<!-- capture: audit-ext.txt|Only analysed|└ -->
```text
⚠️  Only analysed: heic, video.
18 unchanged folders taken from the index, 6 read.
💡 A photo changed in place by another program? 'audit --full' reads every
folder (done anyway for those listed 7 days ago).

♻️  No new or changed file since the last audit: 10 files taken from the cache.
Audit summary
┌─────────────────────────────────────────────────┬────────┐
│ Media files scanned                             │     10 │
│ Groups of identical files                       │      4 │
│ Extra copies that can be set aside              │      4 │
│ Space that can be freed                         │ 5.9 MB │
│ Broken files (empty or unreadable)              │      1 │
│ Re-encoded videos (moved only with --tier near) │      1 │
│ Duration                                        │    0 s │
└─────────────────────────────────────────────────┴────────┘
```

A value without a dot is a category when one has that name, otherwise an extension: `--ext heic`
means the extension. Only photo, RAW and video extensions are accepted: `--ext pdf` is refused. A name close to a category (`--ext photos`) is refused, with the right spelling:
without that check, it would silently analyse nothing.

## Your own categories

Name the lists you type often in the [configuration file](07-configuration-file.md), under
`[scan.categories]`:

```toml
[scan.categories]
phone = ["heic", "jpg", "mov", "mp4"]
web = ["png", "webp", "gif"]
```

Then `--ext phone`, or `extensions = ["phone"]` in `[scan]`. A name holds letters,
digits, `-` and `_`; a category lists extensions, never other categories; `photo`, `raw`,
`video` and `media` cannot be redefined. A category only names a list: each file is still
handled by its extension.

## Files that are not photos or videos

A zip, a Word document or a PDF copied among the family photos is not analysed, but the audit
counts it: one line at its end, nothing when there is none.

```text
🧹 312 files that are not photos or videos (zip, docx, pdf, …) take 4.2 GB in your photo
folders: see 'Intruder files' in the report.
```

The report's **🧹 Intruder files** section gives the totals per extension and the heaviest
folders; `intruders.csv`, next to `plan.csv`, lists every file (path, folder, extension, size,
date). Counting them costs no extra disk read: the audit lists every folder anyway.

- **Nothing is moved**: a document may matter. Delete or move them yourself, or keep them.
- **Protected and backup folders are left out**, and so are the excluded ones (never read).
- **Companions are never intruders**: what follows a photo or a folder of photos, `.xmp`,
  `.aae`, `.thm`, `.json` (Google Takeout), `Thumbs.db`, `desktop.ini`, `.DS_Store`,
  `.picasa.ini`, `.nomedia`, `.lrv` and `.srt` (GoPro, drones). Change the list in `[scan] companions` of the
  [configuration file](07-configuration-file.md): a name, or an extension with its dot, case
  ignored, such as `companions = [".xmp", ".json", "thumbs.db", ".lrv"]`.

---

← [5. Choose which copy stays](05-choose-the-kept-copy.md) · [Documentation](../README.md) · Next: **[7. The configuration file](07-configuration-file.md)** →
