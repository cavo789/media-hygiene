# Sidecar files

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-sidecars.md)

Sidecars are small files next to a photo or a video, holding its metadata or its edits: `.xmp`
(Lightroom, digiKam, darktable), `.aae` (iPhone edits), `.thm` (camcorder thumbnails). A sidecar
belongs to the files of its folder with the same name: `IMG_1.xmp` to `IMG_1.jpg` or
`IMG_1.CR2`, and `IMG_1.CR2.xmp` to `IMG_1.CR2`, case ignored.

- **Next to its photo**, a sidecar is never touched.
- **Its photo is kept**: between identical copies, the one with a sidecar is kept, so it keeps
  its edits. Only a protected or preferred folder comes first. When several copies each have
  their own sidecar, the other [keep rules](05-choose-the-kept-copy.md#how-the-tool-chooses)
  choose among them.
- **Orphan**: once `clean` has deleted or moved every file of the same name next to it (or if
  there was none to begin with), a sidecar is useless. `clean` moves it to the quarantine, never
  deletes it, after checking that no file of the same name has come back. `undo` puts it back;
  `purge` deletes it for good. Without the `/quarantine` mount, orphans stay put.
- **With `--ext`**, the audit looks at some files only: sidecars already alone before the clean
  are left where they are, only those the clean itself leaves alone are moved.
- **Protected folders** are never modified, sidecars included.

The sidecar of a deleted copy is not moved next to the kept one: it becomes an orphan. To keep
another copy *with* its edits, name its folder in [`--prefer`](05-choose-the-kept-copy.md#prefer-a-folder).

In the audit, orphan sidecars are counted on their own line, and the HTML report lists them in
the *Orphan sidecar files* section ([screenshot](04-html-report.md#broken-files-and-orphan-sidecars)).
