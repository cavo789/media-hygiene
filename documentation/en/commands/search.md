# `search`: find a photo by its words

[Documentation](../README.md) › [Commands](../reference-commands.md) › `search` · 🇫🇷 [Français](../../fr/commands/search.md)

## In short

**Find a photo by what you remember of it: a word, a place, a year, a person.**

`search` finds photos by the words [`tags`](tags.md) gave them and the names given in
[`people`](people.md), in a page of your browser: one field, a grid of the photos found, best
first, each with its folder, date and words. With words after the command, it prints the first
matches as a table instead. Photos you pick on the page can be **set aside**: the next
[`clean --decisions`](clean.md) moves them to the quarantine, journaled and undoable.

**When**: after [`tags`](tags.md) (and [`people`](people.md) for the names); again after the new
photos are tagged.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/[cache](../reference-glossary.md#cache) `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene search
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: mount them `:ro`. |
| Needs | `/cache` (the words of `tags`), your folders (to show the photos), and `-p 127.0.0.1:8088:8088` for the page; `/reports` to set photos aside. |
| Writes | The small previews of the grid, in the cache; the photos you set aside, in `decisions.json` of the reports; your albums, in `albums.json` next to it. |
| Undo | Nothing to undo on the page: [`clean --decisions`](clean.md) moves the photos set aside, [`undo`](undo.md) brings them back. |
| With `mh` | `mh search`, `mh search durbuy ours`. |

## Run it

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\reports:/reports" `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene search
```

Open <http://127.0.0.1:8088/>. `/` searches again, the arrows move, a click or Space picks a
photo, Enter or a double click shows it large (with a link to the original), Escape closes it.
Filters: years, a part of the path, the words of one source only. Ctrl+C, or closing its tab, stops the page.

Without a browser (WSL, a script), give the words: `search durbuy ours` prints the first 20 files
as a table.

## Set photos aside

To remove every photo of someone, or of an event: search them (`person:"Ann"`, a year, a word),
pick them (a click or Space on each, or **Pick all N files found**: every file the search finds,
not only the 240 shown), then **Set aside the picked files**.

- Nothing is deleted from the page. The choice is saved at once in `decisions.json` of your
  reports, read back from the disk and shown with its count and size: *37 files set aside
  (412 MB), saved in …: 'clean --decisions' moves them to the quarantine, and remembers them: if
  one comes back (a new copy from the phone), the audit proposes it again.* The photos set aside
  carry a red *marked to set aside* label.
- **Take out of the set aside** takes the files picked back out of it.
- When you stop the page, `search` proposes the next step: `mh clean --decisions`. It asks first
  how many files and how many bytes go (apart from the duplicates), moves them to the
  quarantine, journaled; [`undo`](undo.md) brings them back, [`purge`](purge.md) frees the
  space.
- A file changed since you chose it (another size or date) is left where it is and listed in the
  clean report; a file of a protected folder refuses the whole file, as everywhere.
- The same `decisions.json` holds what [`review`](review.md) decided: both are kept, and one
  `clean --decisions` applies them all.

## Put photos in an album

To show photos to others (on the TV with [`slideshow`](slideshow.md)), gather them in an
**album**: a named list, *Crete 2023*, of photos from any folders. Type its name in **Album** (the
albums already made are proposed), pick the photos (or **Pick all N files found**), then **➕ Add
to the album**.

- An album is a list of references, nothing else: no photo is copied, moved or changed. It is
  saved at once in `albums.json` of your reports, next to `decisions.json` (not in the cache:
  deleting the cache keeps your albums), read back from the disk and shown: *Crete 2023: 42
  files, saved in …. Only this file changed: no photo was copied or moved.*
- It is **not** the set aside: *Set aside* prepares a removal, *Add to the album* a share. Neither
  ever touches the other's list.
- **Take out of the album** takes the picked photos out of the album typed; an album left empty
  is removed.
- A photo moved since, by [`sort`](sort.md), by [`undo`](undo.md), or in a folder renamed in the
  Explorer (once an audit has seen it), is found again by its content: the album follows it. One
  found nowhere (deleted, or in the quarantine) stays in the album, listed as missing, until it
  comes back.
- **📺 Share on the TV** gives the command that shows the album typed, copied for you: stop the
  page, then `mh slideshow --album "Crete 2023" --lan` ([`slideshow`](slideshow.md)).
- **📨 Prepare for sending** gives the command that makes the album ready to send by mail:
  resized copies without the GPS position, a folder and a zip, `mh share --album "Crete 2023"`
  ([`share`](share.md)).
- At most 3,000 photos added at once: narrow a search that finds more.

An album can also become a folder of the Explorer: [`album "Crete 2023"`](album.md) makes it, as
second names (hard links), without a copy.

## What you can type

| You type | It finds |
|---|---|
| `Durbuy ours` | The photos with both words, whatever their source. |
| `noel`, `gateau` | `Noël`, `gâteau`: case and accents do not matter. |
| `bougies` | `bougie` too: the words are kept in the singular. |
| `anniv*` | Every word starting so. |
| `"bord de mer"` | The phrase, its words in that order. |
| `place:durbuy` | The word among the places only; also `vision`, `caption`, `folder`, `name` (the file name), `date`, `person`. |
| `anniversaire` | Also `Anniversaire Léa.mp4`: the words of a file name you chose count too (`IMG_1234` gives none). |
| `neige 2008` | The year is a word of the date: the snow of 2008. |
| `Chloé montagne` | The photos of Chloé with "montagne" from any source, once her group is named in [`people`](people.md). |
| `person:chloe`, `person:"Mamie Jeanne"` | The name among the people only. A name nobody has yet is said in one line. |
| `un chat sur un canapé` | After [`tags --meaning`](tags.md): the photos that show it first, even without any of these words ([search by meaning](../reference-tags.md#find-a-photo-by-what-it-shows---meaning)). |
| `Chloé cuisine` | After `tags --meaning`: the photos of Chloé only, the kitchens first. |

## Options

| Option | What it does |
|---|---|
| `WORDS` | Words to find, printed as a table instead of opening the page. |
| `--limit N` | With words: how many files the table lists at most (20 by default). |
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## Good to know

- Without `/reports` (or with a folder the tool cannot write to), **Set aside the picked files** says why and
  saves nothing; the search itself works.
- The search reads the cache only: run [`audit`](audit.md) then [`tags`](tags.md) again to find
  the new photos.
- Without `/cache`, or with a cache no audit has filled yet, it stops and says why.
- **By meaning**: once [`tags --meaning`](tags.md) gave the photos their vectors, the search
  ranks them by what they show too, and says so at start (*Search by meaning: 52,318 photos can
  be found by what they show.*). The model is read from the cache, never downloaded by `search`.
- The names of the people come from the faces of the cache and the names of `config.toml`, at
  each start: mount `/config` too to find them. Nothing else to run after naming a group.

## Go further

- [Find in short](../find/quick-guide.md)
- [Tags: find a photo by its words](../reference-tags.md#find-a-photo-by-its-words-search)

## The built-in help

<details>
<summary><code>search --help</code></summary>

<!-- capture: help-search.txt -->
```text
 Usage: media-hygiene search [OPTIONS] [words]...

 🔒 Read-only: never changes your photos. Find photos by their words in your
 browser (or as a table): the words 'tags' gave them.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   words      <str>  Words to find, printed as a table instead of opening the │
│                     page: "bord de mer" a phrase, anniv* a start of word,    │
│                     place:durbuy among the places only (also vision,         │
│                     caption, folder, name, date, person).                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --limit          <int range> [x>=1]  How many files the table lists at most. │
│                                      Default: 20.                            │
│ --port           <int range> [x>=1]  Port of the page. docker run publishes  │
│                                      it under the same number on your        │
│                                      computer: -p 127.0.0.1:9000:9000 for    │
│                                      --port 9000. Default:  port in          │
│                                      config.toml, 8088.                      │
│ --help   -h                          Show this message and exit.             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
