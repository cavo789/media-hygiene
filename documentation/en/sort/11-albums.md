# 11. Albums: one photo in several folders, without a copy

[Documentation](../README.md) › Sorting, step 11 · 🇫🇷 [Français](../../fr/sort/11-albums.md)

A tree gives each photo **one** place: `2016/Parties/Christmas` or `2016/Grandma`, never both.
Yet you may want "every Christmas since 2003", "my best photos" or "everything with Grandma" in
one folder, without undoing the tree `sort` built.

`album` gathers such a selection into a folder of **hard links**. A hard link is a second name
for the same file: the photo is neither copied nor moved, and takes no extra space. It is
optional, and changes nothing until you add `--apply`.

## What a hard link is, in Windows

- In Explorer, the album holds ordinary files: open them, print them, send them.
- They are **the same files** as the originals: a photo edited (rotated, retouched) in the album
  is edited in its sorted folder too.
- Deleting a photo from the album leaves the original where it is; deleting the whole album folder
  is safe too.
- The *Properties* of a folder holding both the album and the originals count each photo twice:
  the disk does not. Its free space is what tells.

## Where the albums go

In `config.toml` ([the configuration file](../clean/07-configuration-file.md)), the `[album]`
section names the folder holding the albums; each album is a folder in it:

```toml
[album]
root = 'C:\Photos\Albums'
```

Left empty, the albums go to an `Albums` folder in the `target` of `[classify]`
([step 4](04-classify.md#your-own-structure)).

A hard link never leaves its disk, **nor the folder mounted with `-v`**: two folders mounted
separately are two different places for Docker, even on the same drive. Mount the folder that
holds both your photos and the albums (`C:\Photos` for `C:\Photos\Albums`). `album` checks it
before anything is made, and lists apart the files it cannot link.

## Choose what the album gathers

The selection comes from the plan of the latest `classify` run ([step 4](04-classify.md)), read
with your edits of the workbook and of [the browser page](10-name-events-in-the-browser.md):

| Option | Gathers |
|---|---|
| `--category Christmas` | The files of this category, as the edited workbook says: a category you renamed is asked for under its new name; an event you named gives its files its name. |
| `--event Kermesse` | The files of one event: its name, or its id (the first column of the Events sheet). |
| `--rule Holidays` | The files a rule of [step 6](06-write-down-what-you-know.md) decided, by its `name`. |
| `--rating 4` | The files given at least 4 stars in Windows (1 to 5), as the audit read them: mount the cache. |

Case does not matter. Given together, every option must match: `--category Christmas --rating 4`
gathers the best Christmas photos. `--workbook PATH` reads another `classify` workbook than the
latest.

## Make it

Mount your folders **without** `:ro`, with the cache, the journal, the reports folder of
`classify` and your configuration:

```powershell
docker run --rm -it `
  -v "C:\Photos:/data/c/Photos" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\journal:/journal" `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene album "Christmas" --category Christmas
```

`album` first shows what it would do, and changes nothing:

```text
──────────────────────────────── Album Christmas ───────────────────────────────
Workbook: C:\Users\you\media-hygiene\reports\20261002-123210-classify\classify.xlsx
┌──────────────────────────┬────────────────────────────┐
│ Album folder             │ C:\Photos\Albums\Christmas │
│ Files selected           │                        212 │
│ Links to make            │                        212 │
│ In the album already     │                          0 │
│ Not found                │                          0 │
│ On another disk or mount │                          0 │
└──────────────────────────┴────────────────────────────┘
💡 Nothing was changed: add --apply to make the links.
```

- *Not found*: files no longer where the plan saw them, nor where a `sort` of that plan moved
  them (renamed, deleted since). They are never linked on a guess: run `classify` again.
- *On another disk or mount*: see [where the albums go](#where-the-albums-go).

Add `--apply` to make the links. Each photo keeps its name in the album; two photos of the same
name get ` (2)`, ` (3)`… (`IMG_0001 (2).jpg`).

## Run it again

The same command later adds the new photos only: a photo already in the album, under any name, is
not linked twice. An album never removes a photo by itself; to start it over, undo it or delete
its folder.

## Never seen as duplicates

An album folder holds a small file, `.media-hygiene-album`. `audit`, `clean`, `classify` and
`sort` skip every folder holding it: the photos of an album are never offered as duplicates of
their originals, nor sorted a second time. Keep that file in the album.

## Undo it

An album run is journaled like a sort: `history` lists it (column *Linked*), and
`undo <run>` ([undo](../clean/09-undo-history-purge.md)) removes its links, its
`.media-hygiene-album` file and the folders it created. The originals are not touched.

`undo` removes a link only while the photo still has another name. If the original was deleted
since (by hand, or by `clean`), the photo in the album is the last one left: `undo` keeps it and
says so.

## With sort and clean

- A `sort` on the same disk renames the originals: the album still shows the same photos, and
  `album` finds them where the sort put them.
- A `sort` to **another** disk copies each file there: the album then keeps the old copy, which
  takes space again. Make your albums on the disk of the sorted tree.
- `clean` deleting a photo that is also in an album frees no space while the album holds it.
- A disk that refuses hard links (a FAT or exFAT USB drive, some network shares): `album` stops at
  the first refusal and says why; `undo` removes the empty folder it left.
- Sidecar files (`.xmp`, `.aae`) are not linked: the album holds the photos and videos only.

---

← [10. Name the events in your browser](10-name-events-in-the-browser.md) · [Documentation](../README.md)
