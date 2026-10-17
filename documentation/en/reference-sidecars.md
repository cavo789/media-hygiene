# Sidecar files

[Documentation](README.md) › Reference · 🇫🇷 [Français](../fr/reference-sidecars.md)

Sidecars are small files next to a photo or a video, holding its metadata or its edits: `.xmp`
(Lightroom, digiKam, darktable), `.aae` (iPhone edits), `.thm` (camcorder thumbnails), and
the `.json` files of a [Google Photos Takeout](#google-photos-takeout). A sidecar
belongs to the files of its folder with the same name: `IMG_1.xmp` to `IMG_1.jpg` or
`IMG_1.CR2`, and `IMG_1.CR2.xmp` to `IMG_1.CR2`, case ignored.

- **Next to its photo**, a sidecar is never touched.
- **Its photo is kept**: between identical copies, the one with a sidecar is kept, so it keeps
  its edits. Only a protected or preferred folder comes first. When several copies each have
  their own sidecar, the other [keep rules](clean/05-choose-the-kept-copy.md#how-the-tool-chooses)
  choose among them.
- **Orphan**: once `clean` has deleted or moved every file of the same name next to it (or if
  there was none to begin with), a sidecar is useless. `clean` moves it to the quarantine, never
  deletes it, after checking that no file of the same name has come back. `undo` puts it back;
  `purge` deletes it for good. Without the `/quarantine` mount, orphans stay put.
- **With `--ext`**, the audit looks at some files only: sidecars already alone before the clean
  are left where they are, only those the clean itself leaves alone are moved.
- **Protected folders** are never modified, sidecars included.
- **Written by `xmp`**: a sidecar this tool created for its words, and that nobody edited since,
  holds no edits: it does not make its photo the copy kept ([tags](reference-tags.md#carry-the-words-with-the-photos-xmp)).

The sidecar of a copy set aside is not moved next to the kept one: it becomes an orphan. To keep
another copy *with* its edits, name its folder in [`--prefer`](clean/05-choose-the-kept-copy.md#prefer-a-folder).

In the audit, orphan sidecars are counted on their own line, and the HTML report lists them in
the *Orphan sidecar files* section ([screenshot](clean/04-html-report.md#broken-files-and-orphan-sidecars)).

## Google Photos Takeout

Google Takeout (takeout.google.com) downloads a copy of your Google Photos as ZIP files. Extract
them, then add the extracted folder like any other one (step 3): its photos are compared with
yours, and its `.json` files are handled as sidecars.

- **Each `.json` belongs to its photo or video**: `IMG_1234.jpg.json` (older Takeouts) or
  `IMG_1234.jpg.supplemental-metadata.json` (newer ones), also when Google cut the name short
  (`.supplemental-me.json`, a long photo name cut), moved the number of a duplicate name
  (`IMG_1234.jpg(1).json` for `IMG_1234(1).jpg`) or wrote `_` for `&` and `?`. An edited
  version (`IMG_1234-edited.jpg`) shares its original's `.json`, or has it alone when the
  original is gone.
- **It travels with its photo**: `clean` sets it aside once its photo is gone, `sort` moves it
  with its photo, `undo` puts it back. A `.json` that describes no file of its folder is left
  alone.
- **Its date and place are used**: a photo or video without a date of its own (a video, a
  screenshot, a picture received) is dated by `classify` and `tags` from the `.json`, after its
  own EXIF or video date and before its name; its position counts like a GPS position for the
  `place` and `trip` rules and the place words. The photos themselves are never written to.
  This needs the cache (`/cache`): the `.json` files are read once, during the audit.
- **Year folders** (`Photos from 2019`) are generic folder names: between identical copies, the
  one in an album folder is kept.
- **An edit and its original** are never near duplicates of each other: both stay.

Not checked on a real Takeout (none was at hand): these name rules come from the tools that
read Takeouts. The description of a `.json` does not give words to `search` yet, an edited
version's suffix is recognised in English only (`-edited`), and a `.json` whose cut name was
renumbered by `sort` (` (2)`) no longer finds its photo. Tell us what your Takeout looks like
if it differs.
