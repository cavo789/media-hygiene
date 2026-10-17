# `xmp`: carry the words with the photos

[Documentation](../README.md) › [Commands](../reference-commands.md) › `xmp` · 🇫🇷 [Français](../../fr/commands/xmp.md)

## In short

**See your words in digiKam, darktable, Lightroom or Immich, without any change to the photos
themselves.**

The words of [`tags`](tags.md) live in the [cache](../reference-glossary.md#cache) of this tool. `xmp` writes them into
**sidecars**: small `.xmp` files next to the photos (`IMG_1.jpg.xmp` next to `IMG_1.jpg`).
Without `--apply`, it only shows what it would write.

**When**: after [`tags`](tags.md), and again after each new `tags` run.

**Try it**:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  cavo789/media-hygiene xmp
```

## At a glance

| | |
|---|---|
| Your photos | ✋ Acts with `--apply` only: writes `.xmp` sidecars next to the photos, never into a photo. |
| Needs | `/cache` (the words); with `--apply`, your folders **without** `:ro` and `/journal`. |
| Recommended | `/quarantine` (a sidecar of another application is copied there before it is completed), `/config` (`[tags] xmp_sources`). |
| Writes | The sidecars, the journal. |
| Undo | [`undo <run>`](undo.md) removes the sidecars it created and puts the others back byte for byte. |
| With `mh` | `mh xmp`, `mh xmp --apply`. |

## Run it

First see what it would write (the folders may stay `:ro`), then add `--apply`:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\quarantine:/quarantine" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene xmp --apply
```

## What is written

- The words of the sources in `xmp_sources` (`vision` and `place` by default) into `dc:subject`;
  the model's sentence into `dc:description`.
- With `place`: the town into `photoshop:City`, its country into `photoshop:Country`, your
  personal place into `Iptc4xmpCore:Location`. A name that is two of these at once (Luxembourg, a
  town and a country; a place of yours named like its town) fills both fields.
- With `person` (opt-in, never by default): the names of the people on the photo into
  `Iptc4xmpExt:PersonInImage`; `xmp` warns first, since the names then travel with the photos.
- **A sidecar already there is completed, never replaced**: its edits, its other properties and
  its own words stay. A field another application filled keeps its value.

## A position from the folder's town

Many photos carry no GPS position, but their folder says where they were taken: `2019/Douarnenez`,
`Saint-Jean de Luz`. With this line in `config.toml`, `xmp` gives each of those photos **the
position of the town's centre**, so that a photo manager shows it on its map:

```toml
[tags]
xmp_folder_gps = true
```

- **Approximate**: the centre of the town, not the beach where the photo was taken. That is why
  it is off by default.
- **Which folders**: the same as the [`folder_town` rule](../sort/09-places-from-gps.md) of
  `classify`, whether or not that rule is on: the whole name of the folder is a town of 5,000
  inhabitants or more (case, accents and hyphens aside), never a month or a season,
  `folder_town_ignore` respected.
- **Never over a real position**: a photo with its own GPS position (or one from its Google
  Takeout `.json`) gets nothing; a position another application wrote into the sidecar is kept.
- Written as `exif:GPSLatitude` / `exif:GPSLongitude` (e.g. `48,5.7252N`), with the town and its
  country in `photoshop:City` / `photoshop:Country` when the tags give none. exiftool reads
  these positions; whether your photo manager reads a position from a sidecar: check with it.
- The dry run says how many photos get a position, by town: *37 photos without GPS get the
  position of their folder's town (its centre, approximate): Douarnenez 25, Saint-Jean-de-Luz 12.*
- Turned off again, the next `xmp --apply` takes back the positions it wrote; `undo` too.

## Options

| Option | What it does |
|---|---|
| `--path PATH` | Only the photos below this folder (host path); repeat it for several. |
| `--apply` | Write the sidecars; without it, only show what would be written. |

## Good to know

- **Run it again** after `tags`: the words it wrote and no longer gives are taken back, a word you
  removed in another application is not added again, a sidecar already up to date is not written.
- **Left out**: protected folders, and files with an identical copy (run [`clean`](clean.md)
  first: only the copy kept gets a sidecar).
- **Safe**: each sidecar is journaled, written to a temporary file then renamed, read back and
  checked.
- A sidecar written by `xmp` alone does not count as edits when `clean` chooses the copy kept.

## Go further

- [Find in short](../find/quick-guide.md)
- [Tags: carry the words with the photos](../reference-tags.md#carry-the-words-with-the-photos-xmp)
- [Sidecar files](../reference-sidecars.md)

## The built-in help

<details>
<summary><code>xmp --help</code></summary>

<!-- capture: help-xmp.txt -->
```text
 Usage: media-hygiene xmp [OPTIONS]

 Write the words of 'tags' into .xmp sidecars next to the photos, for digiKam,
 darktable, Lightroom or Immich; never into a photo (journaled, undoable).

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --path           <str>  Only the photos below this folder (host path, as you │
│                         mounted it); repeat it for several. Default: every   │
│                         file of the index.                                   │
│ --apply                 Write the sidecars; without it, only show what would │
│                         be written.                                          │
│ --help   -h             Show this message and exit.                          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
