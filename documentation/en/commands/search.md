# `search`: find a photo by its words

[Documentation](../README.md) › [Commands](../reference-commands.md) › `search` · 🇫🇷 [Français](../../fr/commands/search.md)

## In short

**Find a photo by what you remember of it: a word, a place, a year, a person.**

`search` finds photos by the words [`tags`](tags.md) gave them and the names given in
[`people`](people.md), in a page of your browser: one field, a grid of the photos found, best
first, each with its folder, date and words. With words after the command, it prints the first
matches as a table instead.

**When**: after [`tags`](tags.md) (and [`people`](people.md) for the names); again after the new
photos are tagged.

**Try it**:

```powershell
docker run --rm -it `
  -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene search
```

## At a glance

| | |
|---|---|
| Your photos | 🔒 Never changed: mount them `:ro`. |
| Needs | `/cache` (the words of `tags`), your folders (to show the photos), and `-p 127.0.0.1:8088:8088` for the page. |
| Writes | Only the small previews of the grid, in the cache. |
| Undo | Nothing to undo. |
| With `mh` | `mh search`, `mh search durbuy ours`. |

## Run it

```powershell
docker run --rm -it -p 127.0.0.1:8088:8088 `
  -v "C:\Photos:/data/c/Photos:ro" `
  -v media-hygiene-cache:/cache `
  -v "$HOME\media-hygiene\config:/config" `
  cavo789/media-hygiene search
```

Open <http://127.0.0.1:8088/>. `/` searches again, the arrows move, Enter shows the picture large
(with a link to the original), Escape closes it. Filters: years, a part of the path, the words of
one source only. Ctrl+C stops the page.

Without a browser (WSL, a script), give the words: `search durbuy ours` prints the first 20 files
as a table.

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

## Options

| Option | What it does |
|---|---|
| `WORDS` | Words to find, printed as a table instead of opening the page. |
| `--limit N` | With words: how many files the table lists at most (20 by default). |
| `--port PORT` | Port of the page, 8088 by default; publish the same one. |

## Good to know

- The search reads the cache only: run [`audit`](audit.md) then [`tags`](tags.md) again to find
  the new photos.
- Without `/cache`, or with a cache no audit has filled yet, it stops and says why.
- The names of the people come from the faces of the cache and the names of `config.toml`, at
  each start: mount `/config` too to find them. Nothing else to run after naming a group.

## Go further

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
│                                      --port 9000. Default: 8088.             │
│ --help   -h                          Show this message and exit.             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

</details>

---

← [All commands](../reference-commands.md) · [Documentation](../README.md)
