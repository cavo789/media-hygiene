# `album`: an album as a folder on the disk, without a copy

[Documentation](../README.md) › [Commands](../reference-commands.md) › `album` · 🇫🇷 [Français](../../fr/commands/album.md)

## In short

**Give an album its own folder in the Explorer ("Crete 2023", "My best photos") without copying
a photo: no extra space used.**

An **album** is the named list of photos you make in [`search`](search.md#put-photos-in-an-album),
[`browse`](browse.md) or the burst review, saved in `albums.json`. It has several uses, all under
*Share* in the home page and `mh menu`:

| Use | Command |
|---|---|
| On the TV | [`slideshow --album "Crete 2023"`](slideshow.md) |
| On your phone, at home | [the albums' page](home.md#your-albums-on-the-phone) |
| Ready to send by mail | [`share --album "Crete 2023"`](share.md) |
| A folder of links on the disk | `album "Crete 2023"`, this page |

`album` makes that folder of **hard links**: a second name for the same file, neither copied nor
moved, in one folder whatever folders the photos come from. Without `--apply`, it only shows
what it would do.

**When**: once the album exists, after an [`audit`](audit.md) (a photo of the album moved since
is found again by its content).

**Try it**:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene album "Crete 2023"
```

## At a glance

| | |
|---|---|
| Your photos | ✋ Acts with `--apply` only: adds second names (hard links); no photo is copied, moved nor deleted. |
| Needs | `/reports` (the albums, `albums.json`); with `--apply`, your folders **without** `:ro` and `/journal`. |
| Recommended | `/cache` (to find a photo moved since; needed for `--rating`), `/config` (the `[album]` folder). |
| Writes | The album folder, its links and a `.media-hygiene-album` file; the journal. `albums.json` is only read. |
| Undo | [`undo <run>`](undo.md) removes the links and the folders it created; the originals stay. |
| With `mh` | `mh album "Crete 2023"`. |

## Run it

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene album "Crete 2023"
```

It shows the album folder, the files of the album, the links to make, those already in the
folder, and those it cannot link (*Not found*: moved or deleted since they were added, *On another
disk or mount*), then *💡 Nothing was changed: add --apply to make the links*. Add `--apply` to
make them. The name is the album's, whatever its case: `album "crete 2023"` makes the folder
`Crete 2023`.

## Without an album: a selection of the classify plan

After [`classify`](classify.md), `album` can also gather a selection of its plan, without an
album saved first: `album "Christmas" --category Christmas`. Each option below picks from the
plan **instead of** `albums.json`; given together, every option must match: `--category Christmas
--rating 4` gathers the best Christmas photos. Case does not matter. More:
[Sorting, step 12](../sort/12-albums.md#choose-what-the-album-gathers).

## Options

| Option | What it does |
|---|---|
| `NAME` | The album's name, as `search` and `browse` saved it: the folder holding its links (required). |
| `--category NAME` | Instead of a saved album: the files of this category, as the edited `classify` workbook says. |
| `--event EVENT` | The files of this event: its id (Events sheet) or its name. |
| `--rule NAME` | The files the `[[classify.rules]]` entry of this name decided. |
| `--rating N` | The files given at least N stars (1 to 5) in Windows, as the audit read them. |
| `--workbook PATH` | The `classify` workbook to read; the latest `classify` run's by default. |
| `--apply` | Make the links; without it, only show what the album gathers. |

## Good to know

- **Where the albums go**: `root` in the `[album]` section of `config.toml`; empty, an `Albums`
  folder in the `target` of `[classify]`.
- **A hard link never leaves its disk, nor its `-v`**: mount the folder holding both the photos
  and the albums (`C:\Photos` for `C:\Photos\Albums`).
- **Run it again** later, after adding photos to the album: only the new photos are added; a
  photo is never linked twice. A photo taken out of the album stays in its folder: `undo` the
  run, or delete the link.
- **Never seen as duplicates**: `audit`, `clean`, `classify` and `sort` skip every folder holding
  `.media-hygiene-album`. Keep that file.
- A photo edited in the album is edited in its sorted folder too: it is the same file.
- A disk that refuses hard links (FAT, exFAT, some network shares) stops `album` at the first
  refusal, with the reason.

## Go further

- [`search`: put photos in an album](search.md#put-photos-in-an-album)
- [`share`: the album ready to send](share.md)
- [Sorting, step 12: albums](../sort/12-albums.md)

## The built-in help

<details>
<summary><code>album --help</code></summary>

<!-- capture: help-album.txt -->
```text
 Usage: media-hygiene album [OPTIONS] {name}

 Gather a selection of the classify plan into a folder of hard links: nothing
 is copied nor moved (journaled, undoable).

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    name      <str>  The album's name: the folder holding its links.        │
│                       [required]                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --category          <str>  The files of this category, as the edited         │
│                            workbook says.                                    │
│ --event             <str>  The files of this event: its id or its name.      │
│ --apply                    Make the links; without it, only show what the    │
│                            album gathers.                                    │
│ --help      -h             Show this message and exit.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced options ───────────────────────────────────────────────────────────╮
│ --rule            <str>                  The files the classify rule of this │
│                                          name decided.                       │
│ --rating          <int range> [1<=x<=5]  The files given at least these      │
│                                          stars in Windows (1 to 5).          │
│ --workbook        <str>                  The classify workbook to read; the  │
│                                          latest classify run's by default.   │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Advanced: folders (override folders.* of config.toml) ──────────────────────╮
│ --backup        <str>  A backup or an old disk, mounted read-only: never     │
│                        changed, and not refused for being read-only (mh      │
│                        passes your backups). Repeatable.                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
