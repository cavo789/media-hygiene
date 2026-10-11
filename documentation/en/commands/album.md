# `album`: one photo in several folders, without a copy

[Documentation](../README.md) › [Commands](../reference-commands.md) › `album` · 🇫🇷 [Français](../../fr/commands/album.md)

A tree gives each photo **one** place. `album` gathers a selection ("every Christmas", "my best
photos") into a folder of **hard links**: a second name for the same file. The photo is neither
copied nor moved, and takes no extra space. Without `--apply`, it only shows what it would do.

## At a glance

| | |
|---|---|
| Your photos | ✋ Acts with `--apply` only: adds second names (hard links); no photo is copied, moved nor deleted. |
| Needs | `/reports` (the `classify` run); with `--apply`, your folders **without** `:ro` and `/journal`. |
| Recommended | `/cache` (needed for `--rating`), `/config` (the `[album]` folder). |
| Writes | The album folder, its links and a `.media-hygiene-album` file; the journal. |
| Undo | [`undo <run>`](undo.md) removes the links and the folders it created; the originals stay. |
| With `mh` | `mh album "Christmas" --category Christmas`. |

## Run it

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene album "Christmas" --category Christmas
```

It shows the album folder, the files selected, the links to make, those already in the album, and
those it cannot link (*Not found*, *On another disk or mount*), then *💡 Nothing was changed: add
--apply to make the links*. Add `--apply` to make them.

## Options

| Option | What it does |
|---|---|
| `NAME` | The album's name: the folder holding its links (required). |
| `--category NAME` | The files of this category, as the edited workbook says. |
| `--event EVENT` | The files of this event: its id (Events sheet) or its name. |
| `--rule NAME` | The files the `[[classify.rules]]` entry of this name decided. |
| `--rating N` | The files given at least N stars (1 to 5) in Windows, as the audit read them. |
| `--workbook PATH` | The `classify` workbook to read; the latest `classify` run's by default. |
| `--apply` | Make the links; without it, only show what the album gathers. |

Given together, every option must match: `--category Christmas --rating 4` gathers the best
Christmas photos. Case does not matter.

## Good to know

- **Where the albums go**: `root` in the `[album]` section of `config.toml`; empty, an `Albums`
  folder in the `target` of `[classify]`.
- **A hard link never leaves its disk, nor its `-v`**: mount the folder holding both the photos
  and the albums (`C:\Photos` for `C:\Photos\Albums`).
- **Run it again** later: only the new photos are added; a photo is never linked twice.
- **Never seen as duplicates**: `audit`, `clean`, `classify` and `sort` skip every folder holding
  `.media-hygiene-album`. Keep that file.
- A photo edited in the album is edited in its sorted folder too: it is the same file.
- A disk that refuses hard links (FAT, exFAT, some network shares) stops `album` at the first
  refusal, with the reason.

## Go further

- [Sorting, step 11: albums](../sort/11-albums.md)

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
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
